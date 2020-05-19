from dataclasses import dataclass, field
from myhdl import SignalType, Signal, instances, block, intbv, ConcatSignal, always_comb, always_seq, enum

from utils import num


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


@dataclass
class ByteFifoProducer(FifoProducer):
    data_size: SignalType = field(default=None)
    fill_level: SignalType = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        if self.data_size is None:
            self.data_size = Signal(num.integer(len(self.data) // 8))


@dataclass
class ByteFifoConsumer(FifoConsumer):
    data_size: SignalType = field(default=None)
    fill_level: SignalType = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        if self.data_size is None:
            self.data_size = Signal(num.integer(len(self.data) // 8))


@block
def byte_fifo(clk: SignalType, rst: SignalType, p: ByteFifoProducer, c: ByteFifoConsumer, buffer_size=None):
    """
    Synchrone byte based fifo.
    Number of input and output bytes can be changed dynamically.
    :param clk: clk signal
    :param rst: rst signal
    :param p: all signals of the producer
    :param c: all signals of the consumer
    :param buffer_size: size of internal buffer in bytes
    :return: myhdl instances
    """

    # Operating on a byte base
    assert len(p.data) % 8 == 0
    p_max_data_size = len(p.data) // 8
    assert len(c.data) % 8 == 0
    c_max_data_size = len(c.data) // 8

    # Handle buffer size
    min_buffer_size = p_max_data_size + c_max_data_size
    if buffer_size is None:
        buffer_size = min_buffer_size
    assert buffer_size >= min_buffer_size

    buffer = [Signal(intbv(0, min=0, max=256)) for _ in range(buffer_size)]
    p_addr = Signal(intbv(0, min=0, max=buffer_size))
    c_addr = Signal(intbv(0, min=0, max=buffer_size))
    fill_level = Signal(intbv(0, min=0, max=buffer_size - 1))

    # Prepare max consumer length buffer
    c_data_bytes = [Signal(intbv(0, min=0, max=256)) for _ in range(c_max_data_size)]
    c_data = ConcatSignal(*reversed(c_data_bytes))

    @always_comb
    def calculate_fill_level():
        if p_addr >= c_addr:
            fill_level.next = p_addr - c_addr
        else:
            fill_level.next = buffer_size - c_addr + p_addr

    @always_comb
    def check_full():
        p.full.next = buffer_size - 1 - fill_level < p.data_size

    @always_seq(clk.posedge, reset=rst)
    def handle_wr():
        if p.wr and not p.full:
            for i in range(p_max_data_size):
                if i < p.data_size:
                    byte_addr = i << 3  # * 8
                    if p_addr + i < buffer_size:
                        buffer[p_addr + i].next = p.data[byte_addr + 8:byte_addr]
                    else:
                        buffer[i - (buffer_size - p_addr)].next = p.data[byte_addr + 8:byte_addr]

            if (buffer_size - 1) - p_addr < p.data_size:
                p_addr.next = p.data_size - (buffer_size - p_addr)
            else:
                p_addr.next = p_addr + p.data_size

    t_state = enum('CPY', 'RDY')
    rd_state = Signal(t_state.CPY)

    @always_comb
    def check_empty():
        if rd_state == t_state.CPY:
            c.empty.next = True
        else:
            c.empty.next = fill_level < c.data_size

    @always_seq(clk.posedge, reset=rst)
    def handle_rd():
        if rd_state == t_state.CPY:
            # Provide output data
            for i in range(c_max_data_size):
                if i < c.data_size:
                    if c_addr + i < buffer_size:
                        c_data_bytes[i].next = buffer[c_addr + i]
                    else:
                        c_data_bytes[i].next = buffer[i - (buffer_size - c_addr)]
            if fill_level >= c.data_size:
                rd_state.next = t_state.RDY
        if rd_state == t_state.RDY:
            if c.rd and not c.empty:
                # Increase c_addr
                if (buffer_size - 1) - c_addr < c.data_size:
                    c_addr.next = c.data_size - (buffer_size - c_addr)
                else:
                    c_addr.next = c_addr + c.data_size
                rd_state.next = t_state.CPY

    @always_comb
    def assign_c_data():
        c.data.next = c_data

    if p.fill_level is not None:
        @always_comb
        def assign_p_fill_level():
            p.fill_level.next = fill_level

    if c.fill_level is not None:
        @always_comb
        def assign_c_fill_level():
            c.fill_level.next = fill_level

    return instances()
