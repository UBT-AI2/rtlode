from typing import List

from myhdl import SignalType

from generator import expr_parser
from generator.pipeline import PipeConstant
from generator.vector_utils import vec_mul
from generator.config import StageConfig


class MethodNotExplicit(Exception):
    pass


def stage(
        config: StageConfig,
        h: SignalType,
        x: SignalType,
        y: List[SignalType],
        v: List[List[SignalType]]):
    """
    Implements logic to solve a rk stage.

    :param config: all relevant config parameters for this stage
    :param h: step size
    :param x: current x value
    :param y: current y values
    :param v: all intermediate y values aka v vector
    :return:
    """
    if not config.is_explicit():
        raise MethodNotExplicit()

    step = PipeConstant.from_float(config.c) * h
    rhs_x = x + step
    rhs_y = [y[i] + h * vec_mul(
            [PipeConstant.from_float(el) for el in config.a],
            [el[i] for el in v[:config.stage_index]]
        ) for i in range(config.system_size)]

    return [expr_parser.expr(rhs_expr, {
        'x': rhs_x,
        'y': rhs_y
    }) for rhs_expr in config.components]
