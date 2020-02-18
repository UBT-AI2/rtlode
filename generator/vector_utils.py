from myhdl import block, instances, always_comb, always_seq

import generator.calc
from generator.utils import clone_signal
from generator.flow import FlowControl


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
def reduce_flow(in_vector, op, out, flow: FlowControl, default=0):
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
        if flow.enb:
            out.next = result
            flow.fin.next = True

    if flow.clk is not None:
        calc = always_seq(flow.clk_edge(), flow.rst)(assign_out)
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
    return reduce(in_vector, generator.calc.add, res, clk=clk)


@block
def reduce_sum_flow(in_vector, res, flow: FlowControl):
    """
    Computes the sum of all in_vector elements.
    If clk is provided the propagation delay is 1 clk cycle.
    Only the output is latched, the internal adder are still
    working combinatorical.

    :param in_vector: vector of elements
    :param res: sum off all vector elements
    :param flow: FlowControl sigs
    :return: myhdl instances
    """
    return reduce_flow(in_vector, generator.calc.add, res, flow)
