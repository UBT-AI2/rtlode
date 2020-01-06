from myhdl import block, instances, always_seq, enum, Signal, ResetSignal
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
            out_finished.next = True

    return instances()


@block
def runge_kutta(clk, rst, enable, finished, method, ivp):
    rk_state = enum('RESET', 'WAITING', 'CALCULATING', 'FINISHED')
    state = Signal(rk_state.RESET)

    x = Signal(num.from_float(ivp['x']))
    x_end = Signal(num.from_float(ivp['x_end']))
    y = Signal(num.from_float(ivp['y']))
    h = Signal(num.from_float(ivp['h']))

    stage_reset = ResetSignal(False, True, False)
    stage_ints = [None for i in range(method['stages'])]
    enable_sigs = [Signal(bool(0)) for i in range(method['stages'])]
    v_sigs = []

    for si in range(method['stages']):
        c_a = list(map(num.from_float, method['A'][si]))
        c_c = num.from_float(method['c'][si])

        stage_enable = enable if si == 0 else enable_sigs[si - 1]

        v = Signal(num.default())

        stage_ints[si] = stage(c_a, c_c, clk, stage_reset, stage_enable, x, h, v_sigs, y, enable_sigs[si], v)
        v_sigs.append(v)

    x_n = Signal(num.same_as(x))
    x_add_inst = num.add(x, h, x_n)

    y_lincomb_inst_res = Signal(num.same_as(y))
    y_lincomb_inst = lincomb(list(map(num.from_float, method['b'])), v_sigs, y_lincomb_inst_res)
    y_mul_inst_res = Signal(num.same_as(y))
    y_mul_inst = num.mul(h, y_lincomb_inst_res, y_mul_inst_res)
    y_n = Signal(num.same_as(y))
    y_add_inst = num.add(y, y_mul_inst_res, y_n)

    @always_seq(clk.posedge, reset=rst)
    def calc_final():
        if state == rk_state.RESET:
            if enable:
                state.next = rk_state.WAITING
        elif state == rk_state.WAITING:
            if stage_reset == 1:
                stage_reset.next = False
            elif enable_sigs[method['stages'] - 1]:
                state.next = rk_state.CALCULATING
        elif state == rk_state.CALCULATING:
            state.next = rk_state.CALCULATING
            # All stages finished
            print('%f: %s : %f' % (num.to_float(x_n), list(map(num.to_float, v_sigs)), num.to_float(y_n)))
            x.next = x_n
            y.next = y_n
            stage_reset.next = True
            if x_n > x_end:
                state.next = rk_state.FINISHED
            else:
                state.next = rk_state.WAITING
        elif state == rk_state.FINISHED:
            stage_reset.next = True
            finished.next = True
        # print(enable_sigs)

    return instances()
