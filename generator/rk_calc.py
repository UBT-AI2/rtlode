from typing import List

from myhdl import SignalType

import generator.calc
from generator.pipeline import Pipeline
from generator.utils import clone_signal, bind, assign_flow
from generator.vector_utils.lincomb import lincomb


def pipe_calc_step(
        f: List[SignalType],
        y_i: List[SignalType],
        h: SignalType,
        y: SignalType,
        y_n: SignalType) -> Pipeline:
    """
    Provides a pipeline to calculate a new y value.
    y_n = (f .* y_i) * h + y

    :param f: factors for each y value
    :param y_i: intermediate y values
    :param h: step size
    :param y: old value
    :param y_n: new value
    :return:
    """
    if len(f) == 0:
        return Pipeline().then(bind(assign_flow, y, y_n))

    lincomb_res = clone_signal(y_n)
    mul_res = clone_signal(y_n)

    return Pipeline() \
        .then(
            bind(
                lincomb,
                f,
                y_i,
                lincomb_res
            )
        ) \
        .then(bind(generator.calc.mul, h, lincomb_res, mul_res)) \
        .then(bind(generator.calc.add, y, mul_res, y_n))
