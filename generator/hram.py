from myhdl import block, always_seq, Signal, instances, ConcatSignal, enum, ResetSignal, always_comb

from common.data_desc import get_input_desc, get_output_desc
from common.packed_struct import BitVector
from generator.ccip import CcipClData
from generator.cdc_utils import AsyncFifoProducer, AsyncFifoConsumer
from generator.csr import CsrSignals
from generator.fifo import ByteFifoProducer, ByteFifoConsumer, byte_fifo
from utils import num


@block
def hram_handler(config, cp2af, af2cp, csr: CsrSignals, data_out: AsyncFifoProducer, data_in: AsyncFifoConsumer):
    """
    Logic to handle data stream read and write from / to cpu (host ram).
    :return:
    """
    assert data_out.clk == data_in.clk
    assert data_out.rst == data_in.rst
    clk = data_out.clk

    reset = ResetSignal(True, True, False)

    @always_comb
    def reset_driver():
        reset.next = data_out.rst or not csr.enb

    input_desc = get_input_desc(config.system_size)
    assert len(input_desc) <= len(CcipClData)
    assert len(input_desc) % 8 == 0

    output_desc = get_output_desc(config.system_size)
    assert len(output_desc) <= len(data_in.data)

    # Used to track if all data was processed
    nbr_inputs = Signal(num.integer(0))
    nbr_outputs = Signal(num.integer(0))

    # Incremental counter used for iterating trough host array
    input_addr_offset = Signal(num.integer(0))

    # Currently not completly process read request?
    outstanding_read_request = Signal(bool(0))

    input_finished = Signal(bool(0))
    output_finished = Signal(bool(0))

    @always_comb
    def input_finished_driver():
        input_finished.next = input_addr_offset == csr.buffer_size and not outstanding_read_request

    @always_comb
    def output_finished_driver():
        output_finished.next = input_finished and nbr_outputs == nbr_inputs

    @always_seq(clk.posedge, reset=None)
    def mem_reads_request():
        if reset:
            af2cp.c0.hdr.vc_sel.next = 0
            af2cp.c0.hdr.rsvd1.next = 0
            af2cp.c0.hdr.cl_len.next = 3  # 4 CL's
            af2cp.c0.hdr.req_type.next = 0
            af2cp.c0.hdr.rsvd0.next = 0
            af2cp.c0.hdr.address.next = 0
            af2cp.c0.hdr.mdata.next = 0  # User defined value, returned in response.
            af2cp.c0.valid.next = 0

            input_addr_offset.next = 0
            outstanding_read_request.next = False
        else:
            if chunk_out.wr and not chunk_out.full:
                outstanding_read_request.next = False

            af2cp.c0.hdr.address.next = csr.input_addr + (input_addr_offset << 2)  # * 4 (0b100)
            if not cp2af.c0TxAlmFull and not outstanding_read_request and not input_finished:
                af2cp.c0.valid.next = 1
                # Wait for one request to be received completly and processed
                outstanding_read_request.next = True
                input_addr_offset.next = input_addr_offset + 1
                if input_addr_offset == csr.buffer_size - 1:
                    chunk_out.data_size.next = 256 - csr.buffer_unused_bytes
                else:
                    chunk_out.data_size.next = 256
            else:
                af2cp.c0.valid.next = 0

    # Coding as list would prevent usage in always without forcing array in hdl code
    cl0_data = BitVector(len(CcipClData)).create_instance()
    cl1_data = BitVector(len(CcipClData)).create_instance()
    cl2_data = BitVector(len(CcipClData)).create_instance()
    cl3_data = BitVector(len(CcipClData)).create_instance()
    input_data_chunk = ConcatSignal(cl3_data, cl2_data, cl1_data, cl0_data)

    cl0_rcv = Signal(bool(0))
    cl1_rcv = Signal(bool(0))
    cl2_rcv = Signal(bool(0))
    cl3_rcv = Signal(bool(0))
    cl_rcv_vec = ConcatSignal(cl3_rcv, cl2_rcv, cl1_rcv, cl0_rcv)

    @always_seq(clk.posedge, reset=reset)
    def mem_reads_responses():
        if chunk_out.wr:
            if not chunk_out.full:
                chunk_out.wr.next = False
                cl0_rcv.next = False
                cl1_rcv.next = False
                cl2_rcv.next = False
                cl3_rcv.next = False
        elif cl_rcv_vec == 0b1111:
            chunk_out.wr.next = True
            chunk_out.data.next = input_data_chunk
        elif cp2af.c0.rspValid == 1 and cp2af.c0.hdr.mdata == 0:
            if cp2af.c0.hdr.cl_num == 0:
                cl0_data.next = cp2af.c0.data
                cl0_rcv.next = True
            elif cp2af.c0.hdr.cl_num == 1:
                cl1_data.next = cp2af.c0.data
                cl1_rcv.next = True
            elif cp2af.c0.hdr.cl_num == 2:
                cl2_data.next = cp2af.c0.data
                cl2_rcv.next = True
            elif cp2af.c0.hdr.cl_num == 3:
                cl3_data.next = cp2af.c0.data
                cl3_rcv.next = True

    chunk_out = ByteFifoProducer(BitVector(len(input_data_chunk)).create_instance())
    input_data = ByteFifoConsumer(BitVector(len(input_desc)).create_instance())

    input_fifo = byte_fifo(clk, reset, chunk_out, input_data)

    @always_seq(clk.posedge, reset=None)
    def check_input_data():
        if reset:
            data_out.wr.next = False
            input_data.rd.next = True
            nbr_inputs.next = 0
        else:
            if data_out.wr and not data_out.full:
                # Output data written
                data_out.wr.next = False
                input_data.rd.next = True

            if input_data.rd and not input_data.empty:
                # Data available
                data_out.data.next = input_data.data
                data_out.wr.next = True
                input_data.rd.next = False
                nbr_inputs.next = nbr_inputs + 1

    output_data = ByteFifoProducer(BitVector(len(output_desc)).create_instance())
    chunk_in = ByteFifoConsumer(BitVector(len(input_data_chunk)).create_instance(), fill_level=Signal(num.integer()))

    output_fifo = byte_fifo(clk, reset, output_data, chunk_in)

    @always_seq(clk.posedge, reset=None)
    def copy_output_data():
        if reset:
            data_in.rd.next = True
            output_data.wr.next = False
            nbr_outputs.next = 0
        else:
            if output_data.wr and not output_data.full:
                # Output data written
                output_data.wr.next = False
                data_in.rd.next = True
                nbr_outputs.next = nbr_outputs + 1
            if data_in.rd and not data_in.empty:
                # Input data read
                output_data.data.next = data_in.data
                output_data.wr.next = True
                data_in.rd.next = False

    # Incremental counter used for iterating trough host array
    output_addr_offset = Signal(num.integer(0))
    output_data_chunk = BitVector(len(CcipClData) * 4).create_instance()

    t_write_state = enum('RDY', 'CL0', 'CL1', 'CL2', 'CL3', 'FIN')
    write_state = Signal(t_write_state.RDY)

    @always_seq(clk.posedge, reset=reset)
    def chunk_in_data_size_driver():
        if output_finished and chunk_in.fill_level > 0:
            chunk_in.data_size.next = chunk_in.fill_level
        else:
            chunk_in.data_size.next = 256

    # Host Memory Writes
    @always_seq(clk.posedge, reset=None)
    def mem_writes():
        if reset:
            af2cp.c1.hdr.rsvd2.next = 0
            af2cp.c1.hdr.vc_sel.next = 0
            af2cp.c1.hdr.sop.next = 0
            af2cp.c1.hdr.rsvd1.next = 0
            af2cp.c1.hdr.cl_len.next = 3  # Always 4 CL's
            af2cp.c1.hdr.req_type.next = 0
            af2cp.c1.hdr.rsvd0.next = 0
            af2cp.c1.hdr.address.next = 0
            af2cp.c1.hdr.mdata.next = 0
            af2cp.c1.data.next = 0
            af2cp.c1.valid.next = 0

            write_state.next = t_write_state.RDY
            output_addr_offset.next = 0
            chunk_in.rd.next = True
            csr.fin.next = False
        else:
            if write_state == t_write_state.RDY:
                af2cp.c1.valid.next = 0
                if not chunk_in.empty and not cp2af.c1TxAlmFull:
                    output_data_chunk.next = chunk_in.data
                    chunk_in.rd.next = False
                    write_state.next = t_write_state.CL0
            elif write_state == t_write_state.CL0:
                af2cp.c1.hdr.sop.next = 1
                af2cp.c1.hdr.address.next = csr.output_addr + (output_addr_offset << 2)  # * 4 (0b100)
                af2cp.c1.data.next = output_data_chunk[512:0]
                af2cp.c1.valid.next = 1
                write_state.next = t_write_state.CL1
            elif write_state == t_write_state.CL1:
                af2cp.c1.hdr.sop.next = 0
                af2cp.c1.hdr.address.next = 0b01
                af2cp.c1.data.next = output_data_chunk[1024:512]
                af2cp.c1.valid.next = 1
                write_state.next = t_write_state.CL2
            elif write_state == t_write_state.CL2:
                af2cp.c1.hdr.sop.next = 0
                af2cp.c1.hdr.address.next = 0b10
                af2cp.c1.data.next = output_data_chunk[1536:1024]
                af2cp.c1.valid.next = 1
                write_state.next = t_write_state.CL3
            elif write_state == t_write_state.CL3:
                af2cp.c1.hdr.sop.next = 0
                af2cp.c1.hdr.address.next = 0b11
                af2cp.c1.data.next = output_data_chunk[2048:1536]
                af2cp.c1.valid.next = 1
                output_addr_offset.next = output_addr_offset + 1
                if not output_finished or chunk_in.fill_level > 0:
                    write_state.next = t_write_state.RDY
                    chunk_in.rd.next = True
                else:
                    write_state.next = t_write_state.FIN
                    chunk_in.rd.next = False
                    csr.fin.next = True
            elif write_state == t_write_state.FIN:
                af2cp.c1.valid.next = 0

    return instances()
