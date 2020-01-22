from myhdl import block, instances, always_seq, enum, Signal, ResetSignal

import num
from rk_stage import stage, StageConfig
from utils import FlowControl
from vector_utils import lincomb


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
    v = [[Signal(num.default()) for _ in range(len(components))] for _ in range(method['stages'])]

    for si in range(method['stages']):
        # TODO use parallel stage calc if possible
        stage_enable = enable if si == 0 else enable_sigs[si - 1]

        config = StageConfig(components, method['A'][si], method['c'][si])
        flow = FlowControl(clk, stage_reset, stage_enable, enable_sigs[si])
        stage_ints[si] = stage(config, flow, h, x, y, v)

    x_n = Signal(num.same_as(x))
    x_add_inst = num.add(x, h, x_n)

    y_n = [Signal(num.same_as(y[i])) for i in range(len(components))]
    @block
    def calc_y_n(i):
        y_lincomb_inst_res = Signal(num.same_as(y[i]))
        y_lincomb_inst = lincomb(list(map(num.from_float, method['b'])), [el[i] for el in v], y_lincomb_inst_res)
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
                print('%d %f: %s : %f' % (i, num.to_float(x_n), list(map(num.to_float, [el[i] for el in v])), num.to_float(y_n[i])))
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
