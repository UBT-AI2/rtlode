from myhdl import block, always_seq, always_comb, Signal, intbv

from generator.flow import FlowControl
from utils.num import DOUBLE_MIN_VALUE, DOUBLE_MAX_VALUE, INTEGER_SIZE, FRACTION_SIZE


@block
def add(in_a, in_b, out_c, clk=None):
    def calc():
        out_c.next = in_a + in_b

    if clk is not None:
        calc = always_seq(clk.posedge, reset=None)(calc)
    else:
        calc = always_comb(calc)
    return calc


@block
def add_flow(in_a, in_b, out_c, flow: FlowControl = None):
    enable = flow.enb if flow is not None else True

    def calc():
        if enable:
            out_c.next = in_a + in_b
            flow.fin.next = True

    if flow is not None:
        calc = always_seq(flow.clk_edge(), flow.rst)(calc)
    else:
        calc = always_comb(calc)
    return calc


@block
def sub(in_a, in_b, out_c, clk=None):
    def calc():
        out_c.next = in_a - in_b

    if clk is not None:
        calc = always_seq(clk.posedge, reset=None)(calc)
    else:
        calc = always_comb(calc)
    return calc


@block
def sub_flow(in_a, in_b, out_c, flow: FlowControl = None):
    enable = flow.enb if flow is not None else True

    def calc():
        if enable:
            out_c.next = in_a - in_b
            flow.fin.next = True

    if flow is not None:
        calc = always_seq(flow.clk_edge(), flow.rst)(calc)
    else:
        calc = always_comb(calc)
    return calc


@block
def mul(in_a, in_b, out_c, clk=None):
    reg = Signal(intbv(0, min=DOUBLE_MIN_VALUE, max=DOUBLE_MAX_VALUE))

    @always_comb
    def resize():
        out_c.next = reg[INTEGER_SIZE + FRACTION_SIZE + 1 + FRACTION_SIZE:FRACTION_SIZE].signed()

    def calc():
        reg.next = (in_a * in_b)

    if clk is not None:
        calc = always_seq(clk.posedge, reset=None)(calc)
    else:
        calc = always_comb(calc)
    return [resize, calc]


@block
def mul_flow(in_a, in_b, out_c, flow: FlowControl = None):
    enable = flow.enb if flow is not None else True

    reg = Signal(intbv(0, min=DOUBLE_MIN_VALUE, max=DOUBLE_MAX_VALUE))

    @always_comb
    def resize():
        out_c.next = reg[INTEGER_SIZE + FRACTION_SIZE + 1 + FRACTION_SIZE:FRACTION_SIZE].signed()

    def calc():
        if enable:
            reg.next = (in_a * in_b)
            flow.fin.next = True

    if flow is not None:
        calc = always_seq(flow.clk_edge(), flow.rst)(calc)
    else:
        calc = always_comb(calc)
    return [resize, calc]
