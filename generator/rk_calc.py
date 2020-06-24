from typing import List

from myhdl import SignalType

from generator.pipeline_elements import mul, add, vec_mul


def pipe_calc_step(
        f: List[SignalType],
        y_i: List[SignalType],
        h: SignalType,
        y: SignalType):
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
        return y

    lincomb_res = vec_mul(f, y_i)
    mul_res = mul(h, lincomb_res)
    return add(y, mul_res)
