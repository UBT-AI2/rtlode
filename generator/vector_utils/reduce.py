from myhdl import block, instances, always_comb, always_seq

import generator.calc
from generator.utils import clone_signal
from generator.flow import FlowControl


@block
def reduce(in_vector, op, out, flow: FlowControl = None, default=0):
    """
    Reduces vector with given operator.
    Even if flow is provided the op is not flow controlled. Only the output is latched.

    TODO: Implement tree structure instead of sequential line

    :param in_vector: vector of elements
    :param op: the operation to be applied to each value pair
    :param out: result of reduce operation
    :param default: default value if vector is empty
    :param flow: FlowControl sigs
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

    if flow is not None:
        def assign_out():
            if flow.enb:
                out.next = result
                flow.fin.next = True
        calc = always_seq(flow.clk_edge(), flow.rst)(assign_out)
    else:
        def assign_out():
            out.next = result
        calc = always_comb(assign_out)

    return instances()


@block
def reduce_and(in_vector, res, flow: FlowControl = None):
    """
    Checks if all elements of the vector are true.

    :param in_vector: vector of elements
    :param res: sum off all vector elements
    :param flow: FlowControl sigs
    :return: myhdl instances
    """
    @block
    def logical_and(a, b, c):
        @always_comb
        def assign():
            c.next = a and b
        return instances()

    return reduce(in_vector, logical_and, res, flow=flow, default=1)


@block
def reduce_sum(in_vector, res, flow: FlowControl = None):
    """
    Computes the sum of all in_vector elements.

    :param in_vector: vector of elements
    :param res: sum off all vector elements
    :param flow: FlowControl sigs
    :return: myhdl instances
    """
    return reduce(in_vector, generator.calc.add, res, flow=flow)
