from myhdl import block, Signal, SignalType

import generator.calc
from generator.flow import FlowControl
from generator.pipeline import Pipeline
from generator.utils import bind, assign_flow
from generator.vector_utils.reduce import reduce_sum
from utils import num


class UnequalVectorLength(Exception):
    pass


def lincomb(in_a, in_b, out_sum):
    """
    Calculates the linear combination of vector a and b.

    :param in_a: input vector a
    :param in_b: input vector b
    :param out_sum: sum of a .* b
    :return: pipe instance
    :raises UnequalVectorLength: if lengths of vector a and b are not equal
    """
    if len(in_a) != len(in_b):
        raise UnequalVectorLength("len(in_a) = %d != len(in_b) = %d" % (len(in_a), len(in_b)))
    n_elements = len(in_a)

    # Remove elements where one factor is 0
    valid = [
        (isinstance(in_a[i], SignalType) or in_a[i] != 0)
        and (isinstance(in_b[i], SignalType) or in_b[i] != 0)
        for i in range(n_elements)
    ]
    in_a = [in_a[i] for i in range(n_elements) if valid[i]]
    in_b = [in_b[i] for i in range(n_elements) if valid[i]]
    n_elements = len(in_a)

    pipe = Pipeline()
    if n_elements == 0:
        pipe.then(bind(assign_flow, 0, out_sum))
        return pipe
    elif n_elements == 1:
        partial_results = [out_sum]
    else:
        partial_results = [Signal(num.same_as(out_sum)) for _ in range(n_elements)]

    pipe.then([bind(generator.calc.mul, in_a[i], in_b[i], partial_results[i]) for i in range(n_elements)])
    if n_elements > 1:
        pipe.then(bind(reduce_sum, partial_results, out_sum))

    return pipe
