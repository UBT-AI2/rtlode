from typing import List

from myhdl import block, SignalType

from generator import num, expr_parser
from generator.config import StageConfig
from generator.rk_calc import pipe_calc_step
from generator.utils import clone_signal, clone_signal_structure, bind
from generator.flow import FlowControl
from generator.pipeline import Pipeline


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
    """
    Implements logic to solve a rk stage.

    :param config: all relevant config parameters for this stage
    :param flow:
    :param h: step size
    :param x: current x value
    :param y: current y values
    :param v: all intermediate y values aka v vector
    :return:
    """
    if not config.is_explicit():
        raise MethodNotExplicit()
    pipe = Pipeline()

    rhs_x = clone_signal(x)
    rhs_y = clone_signal_structure(y)

    # rhs_x = c_c * in_h + in_x
    rhs_x_int = clone_signal(x)
    rhs_x_pipe = Pipeline()\
        .then(bind(num.mul_flow, clone_signal(rhs_x_int, value=num.from_float(config.c)), h, rhs_x_int))\
        .then(bind(num.add_flow, x, rhs_x_int, rhs_x))

    pipe.then([pipe_calc_step(
        [clone_signal(v[config.stage_index][i], value=num.from_float(el)) for el in config.a],
        [el[i] for el in v[:config.stage_index]],
        h,
        y[i],
        rhs_y[i]
    ) for i in range(config.system_size)] + [rhs_x_pipe])

    pipe.then([bind(expr_parser.expr, rhs_expr, {
            'x': rhs_x,
            'y': rhs_y
        }, v[config.stage_index][i]) for i, rhs_expr in enumerate(config.components)]
              )

    return pipe.create(flow)
