from myhdl import block, always_seq, Signal, concat, instances, always_comb

from generator.ccip import CcipClData
from generator.cdc_utils import FifoProducer, FifoConsumer
from generator.csr import CsrSignals
from generator.packed_struct import StructDescription, BitVector, List
from generator.utils import clone_signal
from utils import num


def get_input_desc(config):
    class InputData(StructDescription):
        x_start = BitVector(num.TOTAL_SIZE)
        y_start = List(config.system_size, BitVector(num.TOTAL_SIZE))
        h = BitVector(num.TOTAL_SIZE)
        n = BitVector(num.INTEGER_SIZE)
        id = BitVector(num.INTEGER_SIZE)

    return InputData


def get_output_desc(config):
    class OutputData(StructDescription):
        x = BitVector(num.TOTAL_SIZE)
        y = List(config.system_size, BitVector(num.TOTAL_SIZE))
        id = BitVector(num.INTEGER_SIZE)

    return OutputData


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

    input_desc = get_input_desc(config)
    assert len(input_desc) <= len(CcipClData)
    parsed_input_data = input_desc.create_read_instance(cp2af.c0.data(len(input_desc), 0))

    output_desc = get_output_desc(config)
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
            af2cp.c0.hdr.cl_len.next = 0
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

    @always_seq(clk.posedge, reset=reset)
    def mem_reads_responses():
        if cp2af.c0.rspValid == 1 and cp2af.c0.hdr.mdata == 0:
            # Handling of an input package
            if not data_out.full and parsed_input_data.id == next_input_id:
                data_out.data.next = concat(cp2af.c0.data)[len(input_desc):]
                data_out.wr.next = True
                csr.input_ack_id.next = next_input_id
        else:
            data_out.wr.next = False

    next_output_id = clone_signal(csr.output_ack_id)

    @always_comb
    def calc_next_output_id():
        next_output_id.next = csr.output_ack_id + 1

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
            if not data_in.empty and not cp2af.c1TxAlmFull and parsed_output_data.id == next_output_id:
                af2cp.c1.valid.next = 1
                data_in.rd.next = True
            else:
                af2cp.c1.valid.next = 0
                data_in.rd.next = False

    return instances()
