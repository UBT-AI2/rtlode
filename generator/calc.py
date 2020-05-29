from typing import Union

from myhdl import block, always_seq, always_comb, Signal, intbv, SignalType

from generator.flow import FlowControl
from generator.utils import assign_flow
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
def mul(in_a: Union[int, SignalType], in_b: SignalType, out_c, flow: FlowControl):
    reg = Signal(intbv(0, min=DOUBLE_MIN_VALUE, max=DOUBLE_MAX_VALUE))

    if isinstance(in_a, int) and in_a == 0:
        return assign_flow(0, out_c, flow)
    elif isinstance(in_a, int) and bin(in_a).count('1') == 1:
        # This multiplication can be implemented in shifts.
        bin_repr = bin(in_a)
        shift_by = len(bin_repr) - 1 - bin_repr.index('1') - FRACTION_SIZE
        print('Implemented multiplication as shift by: ', shift_by)
        if shift_by == 0:
            return assign_flow(in_b, out_c, flow)
        elif shift_by > 0:
            @always_comb
            def shift_left():
                if flow.enb:
                    out_c.next = in_b << shift_by
                flow.fin.next = flow.enb
            return shift_left
        elif shift_by < 0:
            shift_by = -shift_by

            @always_comb
            def shift_right():
                if flow.enb:
                    out_c.next = in_b >> shift_by
                flow.fin.next = flow.enb
            return shift_right

    @always_comb
    def resize():
        out_c.next = reg[NONFRACTION_SIZE + FRACTION_SIZE + 1 + FRACTION_SIZE:FRACTION_SIZE].signed()

    if isinstance(in_a, int):
        @always_seq(flow.clk_edge(), flow.rst)
        def calc():
            if flow.enb:
                reg.next = (intbv(in_a).signed() * in_b)
                flow.fin.next = True
    else:
        @always_seq(flow.clk_edge(), flow.rst)
        def calc():
            if flow.enb:
                reg.next = (in_a * in_b)
                flow.fin.next = True
    return [resize, calc]
