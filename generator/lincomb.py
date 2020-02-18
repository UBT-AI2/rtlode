from myhdl import block, Signal

import generator.calc
from generator.flow import FlowControl
from generator.pipeline import Pipeline
from generator.utils import bind
from generator.vector_utils import reduce_sum_flow
from utils import num


class UnequalVectorLength(Exception):
    pass


@block
def lincomb_flow(in_a, in_b, out_sum, flow: FlowControl):
    """
    Calculates the linear combination of vector a and b.
    If clk is provided the internal multiplications use sequential
    logic while the reduce sum calculation is still combinatorical.
    The resulting propagation delay is 1 clk cycle.

    :param in_a: input vector a
    :param in_b: input vector b
    :param out_sum: sum of a .* b
    :param flow: FlowControl sigs
    :return: myhdl instances
    :raises UnequalVectorLength: if lengths of vector a and b are not equal
    """
    if len(in_a) != len(in_b):
        raise UnequalVectorLength("len(in_a) = %d != len(in_b) = %d" % (len(in_a), len(in_b)))
    n_elements = len(in_a)

    # TODO ignore elements with constant factor of 0
    partial_results = [Signal(num.same_as(out_sum)) for _ in range(n_elements)]

    pipe = Pipeline()
    pipe.then([bind(generator.calc.mul_flow, in_a[i], in_b[i], partial_results[i]) for i in range(n_elements)])
    pipe.then(bind(reduce_sum_flow, partial_results, out_sum))

    return pipe.create(flow)
