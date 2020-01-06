from myhdl import block, instances, always_seq, enum, Signal
import yaml

import num
from utils import lincomb


@block
def rhs(in_clk, in_x, in_y, out_y):

    @always_seq(in_clk.posedge, reset=None)
    def calc():
        out_y.next = in_y << 1  # * 2

    return instances()


@block
def stage(
        c_a,
        c_c,
        in_clk,
        in_reset,
        in_enable,
        in_x,
        in_h,
        in_v,
        in_y,
        out_finished,
        out_v):
    stage_state = enum('RESET', 'CALCULATING', 'FINISHED')
    state = Signal(stage_state.RESET)

    rhs_x = Signal(num.same_as(in_x))
    rhs_y = Signal(num.same_as(in_y))
    rhs_out = Signal(num.same_as(out_v))
    inst_rhs = rhs(in_clk, rhs_x, rhs_y, rhs_out)

    x_inst_mul_res = Signal(num.same_as(in_x))
    x_inst_mul = num.mul(c_c, in_h, x_inst_mul_res, clk=in_clk)
    x_inst_add = num.add(in_x, x_inst_mul_res, rhs_x)

    y_inst_lincomb_res = Signal(num.same_as(out_v))
    y_inst_lincomb = lincomb(c_a, in_v, y_inst_lincomb_res)
    y_inst_mul_res = Signal(num.same_as(in_y))
    y_inst_mul = num.mul(in_h, y_inst_lincomb_res, y_inst_mul_res, clk=in_clk)
    y_inst_add = num.add(in_y, y_inst_mul_res, rhs_y)

    @always_seq(in_clk.posedge, in_reset)
    def statemachine():
        if state == stage_state.RESET:
            if in_enable:
                state.next = stage_state.CALCULATING
        elif state == stage_state.CALCULATING:
            state.next = stage_state.FINISHED
        elif state == stage_state.FINISHED:
            out_v.next = rhs_out
            out_finished.next = 1

    return instances()


@block
def runge_kutta(enable, method = {}):

    pass


# with open("method.yaml", 'r') as stream:
#     try:
#         print(yaml.safe_load(stream))
#     except yaml.YAMLError as exc:
#         print(exc)
