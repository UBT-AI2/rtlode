from myhdl import block, Signal, instances, always_comb, always_seq

from generator import num
from generator.utils import clone_signal
from generator.flow import FlowControl


class UnequalVectorLength(Exception):
    pass


@block
def reduce(in_vector, op, out, default=0, clk=None):
    """
    Reduces vector with given operator.
    If clk is provided the propagation delay is 1 clk cycle.
    Only the output is latched, the internal operators are still
    working combinatorical.

    :param in_vector: vector of elements
    :param op: the operation to be applied to each value pair
    :param out: result of reduce operation
    :param default: default value if vector is empty
    :param clk: optional clk for output assignment
    :return: myhdl instances
    """
    n_elements = len(in_vector)

    partial_results = [clone_signal(out) for i in range(max(n_elements - 1, 0))]
    op_insts = [None for i in range(max(n_elements - 1, 0))]

    result = clone_signal(out, value=default)
    if n_elements == 1:
        result = in_vector[0]
    elif n_elements >= 2:
        result = partial_results[n_elements - 2]

    for i in range(max(n_elements - 1, 0)):
        if i == 0:
            op_insts[i] = op(in_vector[i], in_vector[i + 1], partial_results[i])
        else:
            op_insts[i] = op(partial_results[i - 1], in_vector[i + 1], partial_results[i])

    def assign_out():
        out.next = result

    if clk is not None:
        calc = always_seq(clk.posedge, reset=None)(assign_out)
    else:
        calc = always_comb(assign_out)

    return instances()


@block
def reduce_and(in_vector, res, clk=None):
    """
    Checks if all elements of the vector are true.
    If clk is provided the propagation delay is 1 clk cycle.
    Only the output is latched, the internal and logic is still
    working combinatorical.

    :param in_vector: vector of elements
    :param res: sum off all vector elements
    :param clk: optional clk for output assignment
    :return: myhdl instances
    """
    @block
    def logical_and(a, b, c):
        @always_comb
        def assign():
            c.next = a and b
        return instances()

    return reduce(in_vector, logical_and, res, default=1, clk=clk)


@block
def reduce_sum(in_vector, res, clk=None):
    """
    Computes the sum of all in_vector elements.
    If clk is provided the propagation delay is 1 clk cycle.
    Only the output is latched, the internal adder are still
    working combinatorical.

    :param in_vector: vector of elements
    :param res: sum off all vector elements
    :param clk: optional clk for output assignment
    :return: myhdl instances
    """
    return reduce(in_vector, num.add, res, clk=clk)


@block
def lincomb(in_a, in_b, out_sum, clk=None):
    """
    Calculates the linear combination of vector a and b.
    If clk is provided the internal multiplications use sequential
    logic while the reduce sum calculation is still combinatorical.
    The resulting propagation delay is 1 clk cycle.

    :param in_a: input vector a
    :param in_b: input vector b
    :param out_sum: sum of a .* b
    :param clk: optional clk for multiplications
    :return: myhdl instances
    :raises UnequalVectorLength: if lengths of vector a and b are not equal
    """
    if len(in_a) != len(in_b):
        raise UnequalVectorLength("len(in_a) = %d != len(in_b) = %d" % (len(in_a), len(in_b)))
    n_elements = len(in_a)

    # TODO ignore elements with constant factor of 0

    mul_insts = [None for i in range(n_elements)]
    partial_results = [Signal(num.same_as(out_sum)) for i in range(n_elements)]

    for i in range(n_elements):
        mul_insts[i] = num.mul(in_a[i], in_b[i], partial_results[i], clk=clk)

    reduce_inst = reduce_sum(partial_results, out_sum)

    return instances()


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
    mul_insts = [None for _ in range(n_elements)]
    mul_flows = [flow.create_subflow(enb=flow.enb) for _ in range(n_elements)]
    partial_results = [Signal(num.same_as(out_sum)) for _ in range(n_elements)]

    for i in range(n_elements):
        mul_insts[i] = num.mul_flow(in_a[i], in_b[i], partial_results[i], flow=mul_flows[i])

    reduce_and_inst = reduce_and([f.fin for f in mul_flows], flow.fin)
    reduce_sum_inst = reduce_sum(partial_results, out_sum)

    return instances()
