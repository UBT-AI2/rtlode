from myhdl import block, always_seq, Signal, concat, instances, always_comb, ConcatSignal, intbv, modbv, SignalType, \
    enum

from common.config import Config
from common.data_desc import get_input_desc, get_output_desc
from common.packed_struct import BitVector
from generator.ccip import CcipClData
from generator.cdc_utils import FifoProducer, FifoConsumer
from generator.csr import CsrSignals
from generator.utils import clone_signal
from utils import num


@block
def data_chunk_parser(
        config: Config,
        data_out: FifoProducer,
        chunk_in: FifoProducer,
        input_ack_id: SignalType,
        drop_rest: SignalType,
        drop_bytes: SignalType):
    """
    Used to parse solver input data from a noncontinious data chunk (4CLs) input.
    :param config: config
    :param data_out: parsed solver input data out
    :param chunk_in: data chunk (4CLs) input
    :param input_ack_id: current ack input id
    :param drop_rest: boolean signal indication if rest of given data chunk should be dropped
    :return: myhdl instances
    """
    assert data_out.clk == chunk_in.clk
    assert data_out.rst == chunk_in.rst
    clk = data_out.clk
    reset = data_out.rst

    data_desc = get_input_desc(config.system_size)
    data_len = len(data_desc)
    assert len(data_out.data) == data_len
    assert data_len % 8 == 0
    data_len_bytes = data_len // 8

    chunk_len = len(CcipClData) * 4
    assert len(chunk_in.data) == chunk_len
    assert chunk_len % 8 == 0
    chunk_len_bytes = chunk_len // 8

    buffer_size = int((chunk_len + data_len) / 8)
    buffer = [Signal(intbv(0, min=0, max=256)) for _ in range(buffer_size)]

    data_out_bytes = [Signal(intbv(0, min=0, max=256)) for _ in range(data_len_bytes)]
    data_out_vec = ConcatSignal(*reversed(data_out_bytes))
    data_out_parsed = data_desc.create_read_instance(data_out_vec)

    wr_addr = Signal(modbv(0, min=0, max=buffer_size))
    rd_addr = Signal(modbv(0, min=0, max=buffer_size))
    fill_level = Signal(intbv(0, min=0, max=buffer_size - 1))

    @always_comb
    def calculate_fill_level():
        if wr_addr >= rd_addr:
            fill_level.next = wr_addr - rd_addr
        else:
            fill_level.next = buffer_size - rd_addr + wr_addr

    @always_comb
    def check_full():
        chunk_in.full.next = buffer_size - 1 - fill_level < chunk_len_bytes

    @always_seq(clk.posedge, reset=reset)
    def handle_wr():
        if chunk_in.wr and not chunk_in.full:
            print('Chunk in, drop_rest: %r' % drop_rest)
            if drop_rest:
                chunk_len_drop_bytes = chunk_len_bytes - drop_bytes
                for i in range(chunk_len_drop_bytes):
                    buffer[(wr_addr + i) % buffer_size].next = \
                        chunk_in.data[chunk_len - i * 8:chunk_len - (i + 1) * 8]
                    print('Data: %r' % (chunk_in.data[chunk_len - i * 8:chunk_len - (i + 1) * 8]))
                wr_addr.next = wr_addr + chunk_len_drop_bytes
            else:
                for i in range(chunk_len_bytes):
                    buffer[(wr_addr + i) % buffer_size].next = \
                        chunk_in.data[chunk_len - i * 8:chunk_len - (i + 1) * 8]
                wr_addr.next = wr_addr + chunk_len_bytes

    enough_data = Signal(bool(0))
    t_state = enum('IDLE', 'PROCESSING', 'WRITING')
    parser_state = Signal(t_state.IDLE)

    @always_comb
    def check_enough_data():
        enough_data.next = fill_level >= data_len_bytes

    @always_seq(clk.posedge, reset=reset)
    def handle_parsing():
        if parser_state == t_state.IDLE:
            # Update data_out_bytes
            for i in range(data_len_bytes):
                data_out_bytes[i].next = buffer[(rd_addr + i) % buffer_size]
            if enough_data:
                parser_state.next = t_state.PROCESSING
        elif parser_state == t_state.PROCESSING:
            print("%r; %r" % (data_out_parsed.id, input_ack_id + 1))
            print("%r" % data_out_bytes)
            if data_out_parsed.id == input_ack_id + 1:
                parser_state.next = t_state.WRITING
                data_out.wr.next = True
            else:
                # Skip data
                parser_state.next = t_state.IDLE
                rd_addr.next = rd_addr + data_len_bytes
        elif parser_state == t_state.WRITING:
            if not data_out.full:
                # Output data written
                parser_state.next = t_state.IDLE
                rd_addr.next = rd_addr + data_len_bytes
                input_ack_id.next = input_ack_id + 1
                data_out.wr.next = False

    @always_comb
    def assign_data_out():
        data_out.data.next = data_out_vec

    return instances()


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
            af2cp.c0.hdr.address.next = csr.input_addr + input_addr_offset * 0b100
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
    data_chunk = ConcatSignal(cl0_data, cl1_data, cl2_data, cl3_data)

    cl0_rcv = Signal(bool(0))
    cl1_rcv = Signal(bool(0))
    cl2_rcv = Signal(bool(0))
    cl3_rcv = Signal(bool(0))
    cl_rcv_vec = ConcatSignal(cl3_rcv, cl2_rcv, cl1_rcv, cl0_rcv)

    @always_seq(clk.posedge, reset=reset)
    def mem_reads_responses():
        if cp2af.c0.rspValid == 1 and cp2af.c0.hdr.mdata == 0:
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

        if cl_rcv_vec == 0b1111 and not chunk_out.full:
            cl0_rcv.next = False
            cl1_rcv.next = False
            cl2_rcv.next = False
            cl3_rcv.next = False
            chunk_out.wr.next = True
            chunk_out.data.next = data_chunk

    chunk_out = FifoProducer(clk, reset, BitVector(len(cl_rcv_vec)).create_instance())
    chunk_parser_inst = data_chunk_parser(config, data_out, chunk_out, csr.input_ack_id, data_chunk_drop)

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
