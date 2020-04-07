from dataclasses import dataclass
from myhdl import block, always_seq, always, Signal, ResetSignal, always_comb, intbv, SignalType, instances

from generator.utils import clone_signal

# TODO Add missing unit tests


@block
def assign(clk, rst, out_val, in_val):
    """
    Sequential assign.
    :param clk: clk
    :param rst: rst
    :param out_val: output
    :param in_val: input
    :return:
    """
    @always_seq(clk.posedge, reset=rst)
    def _assign():
        out_val.next = in_val
    return _assign


@block
def ff_synchronizer(clk, rst, chain_out, chain_in, stages=2, chain_rst_value=0):
    """
    Flip-Flop based synchronizer. Can be used to stabelize signals which are crossing clock domains.
    Generates a chain with ff_stages flip flops. Use only with 1 bit values if you are not certain
    what you are doing!
    :param clk: clock for the flip flops
    :param rst: reset for the flip flops
    :param chain_out: output signal of the chain
    :param chain_in: input signal of the chain
    :param stages: number of flip flops in the chain
    :param chain_rst_value: reset value for the flip flops
    :return: myhdl instances
    """
    ff_values = [chain_in, *[clone_signal(chain_in, value=chain_rst_value) for _ in range(stages - 1)], chain_out]
    return [
        assign(clk, rst, ff_values[stage_index + 1], ff_values[stage_index])
        for stage_index in range(stages)
    ]


@block
def areset_synchronizer(clk, async_rst, sync_rst, min_reset_cycles=2):
    """
    Synchronizer for async reset signals. Uses internally a flip-flop sychronizer.
    :param clk: clock of target domain
    :param async_rst: async reset signal to be synchonized
    :param sync_rst: sync reset signal
    :param min_reset_cycles: min clock cycles the sychronized reset should be high
    :return: myhdl instances
    """
    driver_val = Signal(bool(1))
    rst = ResetSignal(True, True, True)

    ff_inst = ff_synchronizer(clk, rst, sync_rst, driver_val, stages=min_reset_cycles, chain_rst_value=1)

    @always(clk.posedge, async_rst.posedge)
    def synchronize():
        if async_rst:
            rst.next = True
            driver_val.next = 1
        else:
            rst.next = False
            driver_val.next = 0

    return [ff_inst, synchronize]


@dataclass
class FifoProducer:
    clk: SignalType
    rst: SignalType
    data: SignalType
    wr: SignalType
    full: SignalType


@dataclass
class FifoConsumer:
    clk: SignalType
    rst: SignalType
    data: SignalType
    rd: SignalType
    empty: SignalType


@block
def async_fifo(p: FifoProducer, c: FifoConsumer, buffer_size_bits=8):
    """
    Async fifo usable for cdc synchronisation.
    The producer and consumer domains are seperated. The buffer size can be given
    by buffer_size_bits. The resulting size is 2**buffer_size_bits.
    :param p: all signals of the producer
    :param c: all signals of the consumer
    :param buffer_size_bits:
    :return: myhdl instances
    """
    assert len(p.data) == len(c.data)

    buffer_size = 2 ** buffer_size_bits
    addr_max = 2 ** (buffer_size_bits + 1) - 1
    buffer = [clone_signal(p.data) for _ in range(buffer_size)]

    do_write = Signal(bool(0))
    do_read = Signal(bool(0))

    p_wr_addr = Signal(intbv(0, min=0, max=addr_max))
    p_wr_addr_gray = clone_signal(p_wr_addr)
    c_wr_addr_gray = clone_signal(p_wr_addr_gray)
    c_rd_addr = Signal(intbv(0, min=0, max=addr_max))
    c_rd_addr_gray = clone_signal(c_rd_addr)
    p_rd_addr_gray = clone_signal(c_rd_addr_gray)

    @always_comb
    def wr_signal():
        do_write.next = p.wr and not p.full

    @always_seq(p.clk, reset=p.rst)
    def wr_pointer():
        if do_write:
            p_wr_addr.next = p_wr_addr + 1

    @always_seq(p.clk, reset=None)
    def wr():
        if do_write:
            buffer[p_wr_addr[buffer_size_bits:0]].next = p.data

    @always_comb
    def wr_pointer_gray():
        p_wr_addr_gray.next = p_wr_addr ^ (p_wr_addr >> 1)

    cdc_rd_addr = ff_synchronizer(p.clk, None, p_rd_addr_gray, c_rd_addr_gray)

    @always_seq(p.clk, reset=p.rst)
    def check_if_full():
        p.full.next = (p_wr_addr_gray[:buffer_size_bits - 1] == ~p_rd_addr_gray[:buffer_size_bits - 1])\
                      and (p_wr_addr_gray[buffer_size_bits - 1:] == p_rd_addr_gray[buffer_size_bits - 1:])

    @always_comb
    def rd_signal():
        do_read.next = c.rd and not c.empty

    @always_seq(c.clk, reset=c.rst)
    def rd_pointer():
        if do_read:
            c_rd_addr.next = c_rd_addr + 1

    @always_comb
    def rd():
        c.data.next = buffer[c_rd_addr[buffer_size_bits:0]]

    @always_comb
    def rd_pointer_gray():
        c_rd_addr_gray.next = c_rd_addr ^ (c_rd_addr >> 1)

    cdc_wr_addr = ff_synchronizer(c.clk, None, c_wr_addr_gray, p_wr_addr_gray)

    @always_seq(c.clk, reset=c.rst)
    def check_if_empty():
        c.empty.next = c_wr_addr_gray == c_rd_addr_gray

    return instances()
