from typing import List

from myhdl import SignalType

import generator.calc
from generator.pipeline import Pipeline
from generator.utils import clone_signal, bind, assign
from generator.lincomb import lincomb_flow


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
        return Pipeline().then(bind(assign, y, y_n))

    lincomb_res = clone_signal(y_n)
    mul_res = clone_signal(y_n)

    return Pipeline() \
        .then(
            bind(
                lincomb_flow,
                f,
                y_i,
                lincomb_res
            )
        ) \
        .then(bind(generator.calc.mul_flow, h, lincomb_res, mul_res)) \
        .then(bind(generator.calc.add_flow, y, mul_res, y_n))
