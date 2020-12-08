from dataclasses import dataclass, field
from myhdl import SignalType, Signal, instances, block, always_comb, modbv, always

from generator.utils import clone_signal


@dataclass
class FifoProducer:
    data: SignalType
    wr: SignalType = field(default=None)
    full: SignalType = field(default=None)

    def __post_init__(self):
        if self.wr is None:
            self.wr = Signal(bool(0))
        if self.full is None:
            self.full = Signal(bool(1))


@dataclass
class FifoConsumer:
    data: SignalType
    rd: SignalType = field(default=None)
    empty: SignalType = field(default=None)

    def __post_init__(self):
        if self.rd is None:
            self.rd = Signal(bool(0))
        if self.empty is None:
            self.empty = Signal(bool(1))


@block
def fifo(clk: SignalType, rst: SignalType, p: FifoProducer, c: FifoConsumer, buffer_size_bits=4):
    """
    Synchrone byte based fifo.
    Number of input and output bytes can be changed dynamically.
    :param clk: clk signal
    :param rst: rst signal
    :param p: all signals of the producer
    :param c: all signals of the consumer
    :param buffer_size_bits: size of internal buffer
    :return: myhdl instances
    """
    assert len(p.data) == len(c.data)

    buffer_size = 2 ** buffer_size_bits
    addr_max = 2 ** (buffer_size_bits + 1)
    buffer = [clone_signal(p.data) for _ in range(buffer_size)]

    p_addr = Signal(modbv(0, min=0, max=addr_max))
    p_addr_next = Signal(modbv(0, min=0, max=addr_max))
    c_addr = Signal(modbv(0, min=0, max=addr_max))
    c_addr_next = Signal(modbv(0, min=0, max=addr_max))

    do_write = Signal(bool(0))
    do_read = Signal(bool(0))

    @always(clk.posedge)
    def check_full():
        p.full.next = p_addr_next[:buffer_size_bits] != c_addr[:buffer_size_bits]\
                      and p_addr_next[buffer_size_bits:] == c_addr[buffer_size_bits:]

    @always_comb
    def handle_do_wr():
        do_write.next = p.wr and not p.full

    @always_comb
    def handle_wr_addr_next():
        if do_write:
            p_addr_next.next = p_addr + 1
        else:
            p_addr_next.next = p_addr

    @always(clk.posedge)
    def handle_wr_addr():
        if rst:
            p_addr.next = 0
        else:
            p_addr.next = p_addr_next

    @always(clk.posedge)
    def handle_wr():
        if do_write:
            buffer[p_addr[buffer_size_bits:0]].next = p.data

    @always(clk.posedge)
    def check_empty():
        c.empty.next = p_addr == c_addr_next

    @always_comb
    def handle_do_rd():
        do_read.next = c.rd and not c.empty

    @always_comb
    def handle_rd_addr_next():
        if do_read:
            c_addr_next.next = c_addr + 1
        else:
            c_addr_next.next = c_addr

    @always(clk.posedge)
    def handle_rd_addr():
        if rst:
            c_addr.next = 0
        else:
            c_addr.next = c_addr_next

    @always(clk.posedge)
    def handle_rd():
        c.data.next = buffer[c_addr_next[buffer_size_bits:0]]

    return instances()
