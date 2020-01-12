from myhdl import block, instances, always_seq, enum, Signal, ResetSignal

import expr_parser
import num
from vector_utils import lincomb


@block
def rhs_map(components, in_x, in_y, out_y, clk=None):
    n_components = len(components)

    scope = {
        'x': in_x,
        'y': in_y
    }

    rhs_insts = [expr_parser.expr(components[i], scope, out_y[i], clk=clk) for i in range(n_components)]

    return instances()


@block
def stage(
        c_comp,
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
    n_components = len(c_comp)

    stage_state = enum('RESET', 'CALCULATING', 'FINISHED')
    state = Signal(stage_state.RESET)

    rhs_x = Signal(num.same_as(in_x))
    rhs_y = [Signal(num.same_as(in_y[i])) for i in range(n_components)]
    rhs_out = [Signal(num.same_as(out_v[i])) for i in range(n_components)]
    inst_rhs = rhs_map(c_comp, rhs_x, rhs_y, rhs_out, clk=in_clk)

    x_inst_mul_res = Signal(num.same_as(in_x))
    x_inst_mul = num.mul(c_c, in_h, x_inst_mul_res, clk=in_clk)
    x_inst_add = num.add(in_x, x_inst_mul_res, rhs_x)

    @block
    def calc_rhs_y(i):
        y_inst_lincomb_res = Signal(num.same_as(out_v[i]))
        print(i)
        print(c_a)
        print(in_v)
        # TODO Bug here
        y_inst_lincomb = lincomb(c_a, [el[i] for el in in_v], y_inst_lincomb_res)
        y_inst_mul_res = Signal(num.same_as(out_v[i]))
        y_inst_mul = num.mul(in_h, y_inst_lincomb_res, y_inst_mul_res, clk=in_clk)
        y_insts_add = num.add(in_y[i], y_inst_mul_res, rhs_y[i])
        return instances()
    rhs_y_insts = [calc_rhs_y(i) for i in range(n_components)]

    @always_seq(in_clk.posedge, in_reset)
    def statemachine():
        if state == stage_state.RESET:
            if in_enable:
                state.next = stage_state.CALCULATING
        elif state == stage_state.CALCULATING:
            state.next = stage_state.FINISHED
        elif state == stage_state.FINISHED:
            for i in range(n_components):
                out_v[i].next = rhs_out[i]
            out_finished.next = True

    return instances()


@block
def runge_kutta(clk, rst, enable, finished, method, ivp):
    rk_state = enum('RESET', 'WAITING', 'CALCULATING', 'FINISHED')
    state = Signal(rk_state.RESET)

    components = ivp['components']
    x = Signal(num.from_float(ivp['x']))
    n_end = Signal(num.integer(ivp['n']))
    y = [Signal(num.from_float(ivp['y'][i])) for i in range(len(components))]
    h = Signal(num.from_float(ivp['h']))

    stage_reset = ResetSignal(False, True, False)
    stage_ints = [None for i in range(method['stages'])]
    enable_sigs = [Signal(bool(0)) for i in range(method['stages'])]
    v_sigs = []

    for si in range(method['stages']):
        c_a = list(map(num.from_float, method['A'][si]))
        c_c = num.from_float(method['c'][si])

        stage_enable = enable if si == 0 else enable_sigs[si - 1]

        v = [Signal(num.default()) for _ in range(len(components))]

        stage_ints[si] = stage(components, c_a, c_c, clk, stage_reset, stage_enable, x, h, v_sigs, y, enable_sigs[si], v)
        v_sigs.append(v)

    x_n = Signal(num.same_as(x))
    x_add_inst = num.add(x, h, x_n)

    y_n = [Signal(num.same_as(y[i])) for i in range(len(components))]
    @block
    def calc_y_n(i):
        y_lincomb_inst_res = Signal(num.same_as(y[i]))
        y_lincomb_inst = lincomb(list(map(num.from_float, method['b'])), [el[i] for el in v_sigs], y_lincomb_inst_res)
        y_mul_inst_res = Signal(num.same_as(y[i]))
        y_mul_inst = num.mul(h, y_lincomb_inst_res, y_mul_inst_res)
        y_add_inst = num.add(y[i], y_mul_inst_res, y_n[i])
        return instances()
    calc_y_n_insts = [calc_y_n(i) for i in range(len(components))]

    n = Signal(num.same_as(n_end))
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
                n.next = n + 1
        elif state == rk_state.CALCULATING:
            state.next = rk_state.CALCULATING
            # All stages finished
            for i in range(len(components)):
                print('%d %f: %s : %f' % (i, num.to_float(x_n), list(map(num.to_float, [el[i] for el in v_sigs])), num.to_float(y_n[i])))
            x.next = x_n
            for i in range(len(components)):
                y[i].next = y_n[i]
            stage_reset.next = True
            if n >= n_end:
                state.next = rk_state.FINISHED
            else:
                state.next = rk_state.WAITING
        elif state == rk_state.FINISHED:
            stage_reset.next = True
            finished.next = True
        # print(enable_sigs)

    return instances()
