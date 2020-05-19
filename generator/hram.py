from myhdl import block, always_seq, Signal, instances, always_comb, ConcatSignal, intbv, modbv, SignalType, \
    enum

from common.config import Config
from common.data_desc import get_input_desc, get_output_desc
from common.packed_struct import BitVector
from generator.ccip import CcipClData
from generator.cdc_utils import AsyncFifoProducer, AsyncFifoConsumer
from generator.csr import CsrSignals
from generator.fifo import ByteFifoProducer, ByteFifoConsumer, byte_fifo
from generator.utils import clone_signal
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
    reset = data_out.rst

    input_desc = get_input_desc(config.system_size)
    assert len(input_desc) <= len(CcipClData)
    assert len(input_desc) % 8 == 0

    output_desc = get_output_desc(config.system_size)
    assert len(output_desc) <= len(data_in.data)
    parsed_output_data = output_desc.create_read_instance(data_in.data)

    # Host Memory Reads
    polling_clk = Signal(bool(0))
    polling_clk_counter = Signal(num.integer())

    # Drop reaminding byte of data chunk
    data_chunk_drop = Signal(bool(0))

    # Incremental counter used for iterating trough host array
    input_addr_offset = Signal(num.integer(0))

    @always_seq(clk.posedge, reset=reset)
    def polling_clk_driver():
        # Possible race condition (second chunk requested before first one was processed) if clk divide to low
        if polling_clk_counter == 1023:  # Polling clk divider
            polling_clk_counter.next = 0
            polling_clk.next = True
        else:
            polling_clk_counter.next = polling_clk_counter + 1
            polling_clk.next = False

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
        else:
            af2cp.c0.hdr.address.next = csr.input_addr + (input_addr_offset << 2)  # * 4 (0b100)
            if csr.enb and not cp2af.c0TxAlmFull and polling_clk and cl_rcv_vec == 0b0000:
                # Wait for one request to be received completly and processed (cl_rcv_vec == 0b0000)
                af2cp.c0.valid.next = 1
                if input_addr_offset == csr.input_size - 1:
                    input_addr_offset.next = 0
                    # Only working if no race condition (see polling_clk_driver())
                    # Multiple simultanious request not possible currently
                    data_chunk_drop.next = True
                else:
                    input_addr_offset.next = input_addr_offset + 1
                    data_chunk_drop.next = False
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
            if data_chunk_drop:
                chunk_out.data_size = 256 - csr.input_rest_bytes
            else:
                chunk_out.data_size = 256
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
    input_data_parsed = input_desc.create_read_instance(input_data.data)

    input_fifo = byte_fifo(clk, reset, chunk_out, input_data)

    @always_seq(clk.posedge, reset=None)
    def check_input_data():
        if reset:
            csr.input_ack_id.next = 0
            data_out.wr.next = False
            input_data.rd.next = True
        else:
            if data_out.wr and not data_out.full:
                # Output data written
                csr.input_ack_id.next = csr.input_ack_id + 1
                data_out.wr.next = False
                input_data.rd.next = True

            if input_data.rd and not input_data.empty:
                # Data available
                if __debug__:
                    print('INPUT: %r' % input_data_parsed.id)
                if input_data_parsed.id == csr.input_ack_id + 1:
                    data_out.data.next = input_data.data
                    data_out.wr.next = True
                    input_data.rd.next = False

    next_output_id = clone_signal(csr.output_ack_id)

    @always_comb
    def calc_next_output_id():
        next_output_id.next = csr.output_ack_id + 1

    output_data = ByteFifoProducer(BitVector(len(output_desc)).create_instance())
    chunk_in = ByteFifoConsumer(BitVector(len(input_data_chunk)).create_instance())

    output_fifo = byte_fifo(clk, reset, output_data, chunk_in)

    @always_seq(clk.posedge, reset=None)
    def copy_output_data():
        if reset:
            data_in.rd.next = True
            output_data.wr.next = False
        else:
            if output_data.wr and not output_data.full:
                # Output data written
                output_data.wr.next = False
                data_in.rd.next = True
            if data_in.rd and not data_in.empty:
                # Input data read
                output_data.data = data_in.data
                output_data.wr.next = True
                data_in.rd.next = False

    # Incremental counter used for iterating trough host array
    output_addr_offset = Signal(num.integer(0))
    output_data_chunk = BitVector(len(CcipClData) * 4).create_instance()

    t_write_state = enum('RDY', 'CL0', 'CL1', 'CL2', 'CL3')
    write_state = Signal(t_write_state.RDY)

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

            output_addr_offset.next = 0

            write_state.next = t_write_state.RDY

            chunk_in.rd.next = False
        else:
            if write_state == t_write_state.RDY:
                af2cp.c1.valid.next = 0
                # TODO set chunk_in.rd
                # TODO increment output_addr_offset
                # TODO check output id
                # if parsed_output_data.id == next_output_id:
                if not chunk_in.empty and not cp2af.c1TxAlmFull:
                    output_data_chunk.next = chunk_in.data
                    chunk_in.rd.next = False
                    write_state.next = t_write_state.CL0
            elif write_state == t_write_state.CL0:
                af2cp.c1.hdr.sop.next = 1
                af2cp.c1.hdr.address.next = csr.output_addr + (output_addr_offset << 2)  # * 4 (0b100)
                af2cp.c1.data.next = chunk_in.data  # TODO
                af2cp.c1.valid.next = 1
            elif write_state == t_write_state.CL1:
                af2cp.c1.hdr.sop.next = 0
                af2cp.c1.hdr.address.next = 0b01
                af2cp.c1.valid.next = 1
            elif write_state == t_write_state.CL2:
                af2cp.c1.hdr.sop.next = 0
                af2cp.c1.hdr.address.next = 0b10
                af2cp.c1.valid.next = 1
            elif write_state == t_write_state.CL3:
                af2cp.c1.hdr.sop.next = 0
                af2cp.c1.hdr.address.next = 0b11
                af2cp.c1.valid.next = 1

    return instances()
