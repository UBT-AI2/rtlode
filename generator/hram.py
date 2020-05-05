from myhdl import block, always_seq, Signal, concat, instances, always_comb, ConcatSignal

from common.data_desc import get_input_desc, get_output_desc
from common.packed_struct import BitVector
from generator.ccip import CcipClData
from generator.cdc_utils import FifoProducer, FifoConsumer
from generator.csr import CsrSignals
from generator.utils import clone_signal
from utils import num


@block
def hram_handler(config, cp2af, af2cp, csr: CsrSignals, data_out: FifoProducer, data_in: FifoConsumer):
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

    parsed_input_raw = BitVector(len(input_desc)).create_instance()
    parsed_input_data = input_desc.create_read_instance(parsed_input_raw)

    @always_comb
    def assign_input():
        parsed_input_raw.next = concat(cp2af.c0.data)[len(input_desc):]

    output_desc = get_output_desc(config.system_size)
    assert len(output_desc) <= len(data_in.data)
    parsed_output_data = output_desc.create_read_instance(data_in.data)

    # Host Memory Reads
    polling_clk = Signal(bool(0))
    polling_clk_counter = Signal(num.integer())

    @always_seq(clk.posedge, reset=reset)
    def polling_clk_driver():
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
        else:
            af2cp.c0.hdr.address.next = csr.input_addr
            if csr.enb and not cp2af.c0TxAlmFull and polling_clk:
                af2cp.c0.valid.next = 1
            else:
                af2cp.c0.valid.next = 0

    next_input_id = clone_signal(csr.input_ack_id)

    @always_comb
    def calc_next_input_id():
        next_input_id.next = csr.input_ack_id + 1

    # Coding as list would prevent usage in always without forcing array in hdl code
    cl0_data = BitVector(len(CcipClData)).create_instance()
    cl1_data = BitVector(len(CcipClData)).create_instance()
    cl2_data = BitVector(len(CcipClData)).create_instance()
    cl3_data = BitVector(len(CcipClData)).create_instance()
    data_chunk = ConcatSignal(cl0_data, cl1_data, cl2_data, cl3_data)

    cl0_rcv = Signal(bool(0))
    cl1_rcv = Signal(bool(0))
    cl2_rcv = Signal(bool(0))
    cl3_rcv = Signal(bool(0))
    cl_rcv_vec = ConcatSignal(cl3_rcv, cl2_rcv, cl1_rcv, cl0_rcv)

    @always_seq(clk.posedge, reset=reset)
    def mem_reads_responses():
        if cp2af.c0.rspValid == 1 and cp2af.c0.hdr.mdata == 0 and parsed_input_data.id == next_input_id:
            data_out.data.next = concat(cp2af.c0.data)[len(input_desc):]
            data_out.wr.next = True
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
        else:
            data_out.wr.next = False

        if data_out.wr and not data_out.full:
            csr.input_ack_id.next = next_input_id

    next_output_id = clone_signal(csr.output_ack_id)

    @always_comb
    def calc_next_output_id():
        next_output_id.next = csr.output_ack_id + 1

    @always_seq(clk.posedge, reset=reset)
    def data_chunk_parser():
        if cl_rcv_vec == 0b1111:
            # All cl's received
            pass

    # Host Memory Writes
    @always_seq(clk.posedge, reset=None)
    def mem_writes():
        if reset:
            af2cp.c1.hdr.rsvd2.next = 0
            af2cp.c1.hdr.vc_sel.next = 0
            af2cp.c1.hdr.sop.next = 0
            af2cp.c1.hdr.rsvd1.next = 0
            af2cp.c1.hdr.cl_len.next = 0
            af2cp.c1.hdr.req_type.next = 0
            af2cp.c1.hdr.rsvd0.next = 0
            af2cp.c1.hdr.address.next = 0
            af2cp.c1.hdr.mdata.next = 0
            af2cp.c1.data.next = 0
            af2cp.c1.valid.next = 0

            data_in.rd.next = False
        else:
            af2cp.c1.hdr.sop.next = 1
            af2cp.c1.hdr.address.next = csr.output_addr
            af2cp.c1.data.next = data_in.data

            # TODO performance optimization possible
            if data_in.rd and not data_in.empty:
                af2cp.c1.valid.next = 1
                data_in.rd.next = False
            else:
                af2cp.c1.valid.next = 0

                if not cp2af.c1TxAlmFull and parsed_output_data.id == next_output_id:
                    data_in.rd.next = True
                else:
                    data_in.rd.next = False

    return instances()
