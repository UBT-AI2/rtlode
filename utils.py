from myhdl import block, Signal, instances, always_comb, always_seq

import num


class UnequalVectorLength(Exception):
    pass


@block
def reduce_sum(in_vector, out_sum, clk=None):
    """
    Computes the sum of all in_vector elements.
    If clk is provided the propagation delay is 1 clk cycle.
    Only the output is latched, the internal adder are still
    working combinatorical.

    :param in_vector: vector of elements
    :param out_sum: sum off all vector elements
    :param clk: optional clk for output assignment
    :return: myhdl instances
    """
    n_elements = len(in_vector)

    partial_sums = [Signal(num.same_as(out_sum)) for i in range(max(n_elements - 1, 0))]
    add_insts = [None for i in range(max(n_elements - 1, 0))]

    result = Signal(num.same_as(out_sum, val=0))
    if n_elements == 1:
        result = in_vector[0]
    elif n_elements >= 2:
        result = partial_sums[n_elements - 2]

    for i in range(max(n_elements - 1, 0)):
        if i == 0:
            add_insts[i] = num.add(in_vector[i], in_vector[i + 1], partial_sums[i])
        else:
            add_insts[i] = num.add(partial_sums[i - 1], in_vector[i + 1], partial_sums[i])

    def assign_out():
        out_sum.next = result

    if clk is not None:
        calc = always_seq(clk.posedge, reset=None)(assign_out)
    else:
        calc = always_comb(assign_out)

    return instances()


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

    mul_insts = [None for i in range(n_elements)]
    partial_results = [Signal(num.same_as(out_sum)) for i in range(n_elements)]

    for i in range(n_elements):
        mul_insts[i] = num.mul(in_a[i], in_b[i], partial_results[i], clk=clk)

    reduce_inst = reduce_sum(partial_results, out_sum)

    return instances()
