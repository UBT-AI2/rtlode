from typing import List

from myhdl import block, SignalType, instances

import expr_parser
import num
from config import StageConfig
from utils import FlowControl, clone_signal, clone_signal_structure, Pipeline
from vector_utils import reduce_and, lincomb_flow


class MethodNotExplicit(Exception):
    pass


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

    # rhs_x = c_c * in_h + in_x
    rhs_x_int = clone_signal(x)
    rhs_x_subflow = flow.create_subflow(enb=flow.enb)
    insts.append(
        Pipeline(rhs_x_subflow)
        .append(num.mul_flow, clone_signal(rhs_x_int, value=num.from_float(config.c)), h, rhs_x_int)
        .append(num.add_flow, x, rhs_x_int, rhs_x)
        .create()
    )

    rhs_y_subflows = [flow.create_subflow(enb=flow.enb) for _ in range(config.system_size)]
    @block
    def calc_rhs_y(index):
        y_inst_lincomb_res = clone_signal(v[config.stage_index][index])
        y_inst_mul_res = clone_signal(v[config.stage_index][index])

        return Pipeline(rhs_y_subflows[index])\
            .append(
                lincomb_flow,
                [clone_signal(v[config.stage_index][index], value=num.from_float(el)) for el in config.a],
                [el[index] for el in v[:config.stage_index]],
                y_inst_lincomb_res
            )\
            .append(num.mul_flow, h, y_inst_lincomb_res, y_inst_mul_res)\
            .append(num.add_flow, y[index], y_inst_mul_res, rhs_y[index])\
            .create()
    insts.append([calc_rhs_y(i) for i in range(config.system_size)])

    rhs_enb = clone_signal(flow.enb)
    rhs_subflows = [flow.create_subflow(enb=rhs_enb) for _ in range(config.system_size)]
    insts.append([reduce_and([rhs_x_subflow.fin] + [sf.fin for sf in rhs_y_subflows], rhs_enb)])
    insts.append([expr_parser.expr(rhs_expr, {
            'x': rhs_x,
            'y': rhs_y
        }, v[config.stage_index][i], flow=rhs_subflows[i]) for i, rhs_expr in enumerate(config.components)]
    )
    insts.append([reduce_and([sf.fin for sf in rhs_subflows], flow.fin)])

    return instances()
