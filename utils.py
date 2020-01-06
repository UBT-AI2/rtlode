from myhdl import block, Signal, instances, always_comb, intbv

import num


@block
def reduce_sum(in_vector, out_sum):
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
            add_insts[i] = num.add_comb(in_vector[i], in_vector[i + 1], partial_sums[i])
        else:
            add_insts[i] = num.add_comb(partial_sums[i - 1], in_vector[i + 1], partial_sums[i])

    @always_comb
    def assign_out():
        out_sum.next = result

    return instances()


@block
def lincomb(in_a, in_b, out_sum, clk=None):
    n_elements = len(in_a)

    mul_insts = [None for i in range(n_elements)]
    partial_results = [Signal(num.same_as(out_sum)) for i in range(n_elements)]

    for i in range(n_elements):
        mul_insts[i] = num.mul(in_a[i], in_b[i], partial_results[i], clk=clk)

    reduce_inst = reduce_sum(partial_results, out_sum)

    return instances()
