from myhdl import block, always_seq, always_comb, Signal, intbv

from generator.flow import FlowControl
from utils.num import DOUBLE_MIN_VALUE, DOUBLE_MAX_VALUE, NONFRACTION_SIZE, FRACTION_SIZE


@block
def add(in_a, in_b, out_c, flow: FlowControl = None):
    if flow is not None:
        def calc():
            if flow.enb:
                out_c.next = in_a + in_b
                flow.fin.next = True
        calc = always_seq(flow.clk_edge(), flow.rst)(calc)
    else:
        def calc():
            out_c.next = in_a + in_b
        calc = always_comb(calc)
    return calc


@block
def sub(in_a, in_b, out_c, flow: FlowControl = None):
    if flow is not None:
        def calc():
            if flow.enb:
                out_c.next = in_a - in_b
                flow.fin.next = True
        calc = always_seq(flow.clk_edge(), flow.rst)(calc)
    else:
        def calc():
            out_c.next = in_a - in_b
        calc = always_comb(calc)
    return calc


@block
def mul(in_a, in_b, out_c, flow: FlowControl = None):
    enable = flow.enb if flow is not None else True

    reg = Signal(intbv(0, min=DOUBLE_MIN_VALUE, max=DOUBLE_MAX_VALUE))

    @always_comb
    def resize():
        out_c.next = reg[NONFRACTION_SIZE + FRACTION_SIZE + 1 + FRACTION_SIZE:FRACTION_SIZE].signed()

    if flow is not None:
        def calc():
            if flow.enb:
                reg.next = (in_a * in_b)
                flow.fin.next = True
        calc = always_seq(flow.clk_edge(), flow.rst)(calc)
    else:
        def calc():
            reg.next = (in_a * in_b)
        calc = always_comb(calc)
    return [resize, calc]
