from typing import List

from myhdl import block, SignalType, Signal, enum, always_seq, instances

import expr_parser
import num
from utils import FlowControl, clone_signal, clone_signal_structure
from vector_utils import lincomb


class MethodNotExplicit(Exception):
    pass


class StageConfig:
    def __init__(self, components: List[str], a: List[float], c: float):
        self.components = components
        self.a = a
        self.c = c
        self.stage_index = len(a)
        self.system_size = len(components)
        # TODO Check if config is wellformed

    def is_explicit(self):
        for i, f in enumerate(self.a):
            if f != 0 and i >= self.stage_index:
                return False
        return True


@block
def stage(
        config: StageConfig,
        flow: FlowControl,
        h: SignalType,
        x: SignalType,
        y: List[SignalType],
        v: List[List[SignalType]]):
    if not config.is_explicit():
        raise MethodNotExplicit()

    insts = []

    rhs_x = clone_signal(x)
    rhs_y = clone_signal_structure(y)
    rhs_out = clone_signal_structure(v[config.stage_index])
    insts.append(
        [expr_parser.expr(rhs_expr, {
            'x': rhs_x,
            'y': rhs_y
        }, rhs_out[i], clk=flow.clk) for i, rhs_expr in enumerate(config.components)]
    )

    # rhs_x = c_c * in_h + in_x
    rhs_x_int = clone_signal(x)
    insts.append([
        num.mul(num.from_float(config.c), h, rhs_x_int, clk=flow.clk),
        num.add(x, rhs_x_int, rhs_x)
    ])

    @block
    def calc_rhs_y(index):
        y_inst_lincomb_res = clone_signal(v[config.stage_index][index])
        y_inst_mul_res = clone_signal(v[config.stage_index][index])
        return [
            lincomb(
                [num.from_float(el) for el in config.a],
                [el[index] for el in v[:config.stage_index]],
                y_inst_lincomb_res
            ),
            num.mul(h, y_inst_lincomb_res, y_inst_mul_res, clk=flow.clk),
            num.add(y[index], y_inst_mul_res, rhs_y[index])
        ]
    insts.append([calc_rhs_y(i) for i in range(config.system_size)])

    stage_state = enum('RESET', 'CALCULATING', 'FINISHED')
    state = Signal(stage_state.RESET)

    @always_seq(flow.clk.posedge, flow.rst)
    def statemachine():
        if state == stage_state.RESET:
            if flow.enb:
                state.next = stage_state.CALCULATING
        elif state == stage_state.CALCULATING:
            state.next = stage_state.FINISHED
        elif state == stage_state.FINISHED:
            for i in range(config.system_size):
                v[config.stage_index][i].next = rhs_out[i]
            flow.fin.next = True

    return instances()
