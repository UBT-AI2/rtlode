from dataclasses import dataclass, field
from myhdl import block, always_seq, always, Signal, ResetSignal, always_comb, SignalType, instances, modbv

from framework.fifo import FifoProducer, FifoConsumer
from generator.utils import clone_signal


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
    Flip-Flop based synchronizer. Can be used to stabilize signals which are crossing clock domains.
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
    ff_values = [chain_in, *[clone_signal(chain_in, reset_value=chain_rst_value) for _ in range(stages - 1)], chain_out]
    return [
        assign(clk, rst, ff_values[stage_index + 1], ff_values[stage_index])
        for stage_index in range(stages)
    ]


@block
def areset_synchronizer(clk, async_rst, sync_rst, min_reset_cycles=2):
    """
    Synchronizer for async reset signals. Uses internally a flip-flop synchronizer.
    :param clk: clock of target domain
    :param async_rst: async reset signal to be synchronized
    :param sync_rst: sync reset signal
    :param min_reset_cycles: min clock cycles the synchronized reset should be high
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
class AsyncFifoProducer(FifoProducer):
    clk: SignalType = field(default=None)
    rst: SignalType = field(default=None)

    def __post_init__(self):
        assert self.clk is not None
        assert self.rst is not None
        super().__post_init__()


@dataclass
class AsyncFifoConsumer(FifoConsumer):
    clk: SignalType = field(default=None)
    rst: SignalType = field(default=None)

    def __post_init__(self):
        assert self.clk is not None
        assert self.rst is not None
        super().__post_init__()


@block
def async_fifo(p: AsyncFifoProducer, c: AsyncFifoConsumer, buffer_size_bits=8):
    """
    Async fifo usable for cdc synchronisation.
    The producer and consumer domains are separated. The buffer size can be given
    by buffer_size_bits. The resulting size is 2^buffer_size_bits.
    :param p: all signals of the producer
    :param c: all signals of the consumer
    :param buffer_size_bits:
    :return: myhdl instances
    """
    assert len(p.data) == len(c.data)

    buffer_size = 2 ** buffer_size_bits
    buffer = [clone_signal(p.data) for _ in range(buffer_size)]

    do_write = Signal(bool(0))
    do_read = Signal(bool(0))

    p_wr_addr = Signal(modbv(0)[buffer_size_bits + 1:])
    p_wr_addr_next = clone_signal(p_wr_addr)
    p_wr_addr_gray = clone_signal(p_wr_addr)
    p_wr_addr_gray_next = clone_signal(p_wr_addr)
    p_rd_addr_gray = clone_signal(p_wr_addr)
    p_full_next = Signal(bool(1))
    c_rd_addr = Signal(modbv(0)[buffer_size_bits + 1:])
    c_rd_addr_next = clone_signal(c_rd_addr)
    c_rd_addr_gray = clone_signal(c_rd_addr)
    c_rd_addr_gray_next = clone_signal(c_rd_addr)
    c_wr_addr_gray = clone_signal(c_rd_addr)
    c_empty_next = Signal(bool(1))

    @always_comb
    def wr_signal():
        do_write.next = p.wr and not p.full

    @always_comb
    def wr_pointer_next():
        if do_write:
            p_wr_addr_next.next = (p_wr_addr + 1)[buffer_size_bits + 1:]
        else:
            p_wr_addr_next.next = p_wr_addr

    @always_comb
    def wr_pointer_gray_next():
        p_wr_addr_gray_next.next = p_wr_addr_next ^ (p_wr_addr_next >> 1)

    @always_seq(p.clk.posedge, reset=p.rst)
    def wr_pointer():
        p_wr_addr.next = p_wr_addr_next
        p_wr_addr_gray.next = p_wr_addr_gray_next

    @always_seq(p.clk.posedge, reset=None)
    def wr():
        if do_write:
            buffer[p_wr_addr[buffer_size_bits:0]].next = p.data

    cdc_rd_addr = ff_synchronizer(p.clk, p.rst, p_rd_addr_gray, c_rd_addr_gray)

    @always_comb
    def full_next():
        p_full_next.next = (p_wr_addr_gray_next[:buffer_size_bits - 1] == (p_rd_addr_gray[:buffer_size_bits - 1] ^ 0b11)) \
                      and (p_wr_addr_gray_next[buffer_size_bits - 1:] == p_rd_addr_gray[buffer_size_bits - 1:])

    @always_seq(p.clk.posedge, reset=p.rst)
    def check_full():
        p.full.next = p_full_next

    @always_comb
    def rd_signal():
        do_read.next = c.rd and not c.empty

    @always_comb
    def rd_pointer_next():
        if do_read:
            c_rd_addr_next.next = (c_rd_addr + 1)[buffer_size_bits + 1:]
        else:
            c_rd_addr_next.next = c_rd_addr

    @always_comb
    def rd_pointer_gray_next():
        c_rd_addr_gray_next.next = c_rd_addr_next ^ (c_rd_addr_next >> 1)

    @always_seq(c.clk.posedge, reset=c.rst)
    def rd_pointer():
        c_rd_addr.next = c_rd_addr_next
        c_rd_addr_gray.next = c_rd_addr_gray_next

    @always_comb
    def rd():
        c.data.next = buffer[c_rd_addr[buffer_size_bits:0]]

    cdc_wr_addr = ff_synchronizer(c.clk, c.rst, c_wr_addr_gray, p_wr_addr_gray)

    @always_comb
    def empty_next():
        c_empty_next.next = c_wr_addr_gray == c_rd_addr_gray_next

    @always_seq(c.clk.posedge, reset=c.rst)
    def check_if_empty():
        c.empty.next = c_empty_next

    return instances()
