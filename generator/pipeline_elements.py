from myhdl import Signal, block, always_seq, instances, SignalType, intbv

from generator.pipeline import InnerNode
from generator.utils import clone_signal
from utils import num
from utils.num import FRACTION_SIZE, NONFRACTION_SIZE


def mul(a, b):
    # if isinstance(a, int) and a == 0:
    #     return 0
    # elif isinstance(a, int) and bin(a).count('1') == 1:
    #     # This multiplication can be implemented in shifts.
    #     bin_repr = bin(a)
    #     shift_by = len(bin_repr) - 1 - bin_repr.index('1') - FRACTION_SIZE
    #     print('Implemented multiplication as shift by: ', shift_by)
    #     if shift_by == 0:
    #         return b
    #     elif shift_by > 0:
    #         @always_comb
    #         def shift_left():
    #             if flow.enb:
    #                 out_c.next = in_b << shift_by
    #             flow.fin.next = flow.enb
    #         return shift_left
    #     elif shift_by < 0:
    #         shift_by = -shift_by
    #
    #         @always_comb
    #         def shift_right():
    #             if flow.enb:
    #                 out_c.next = in_b >> shift_by
    #             flow.fin.next = flow.enb
    #         return shift_right

    node = InnerNode()

    node.add_input(a=a, b=b)
    res = Signal(num.default())
    node.add_output(res)

    @block
    def mul(clk, stage, node_input, node_output):
        reg_max = 2 ** (NONFRACTION_SIZE + 2 * FRACTION_SIZE)
        reg_data = clone_signal(node_output.default)

        @always_seq(clk.posedge, reset=None)
        def drive_data():
            if stage.data2out:
                node_output.default.next = intbv(
                    node_input.a * node_input.b,
                    min=-reg_max,
                    max=reg_max)[1 + NONFRACTION_SIZE + 2 * FRACTION_SIZE:FRACTION_SIZE].signed()
            if stage.reg2out:
                node_output.default.next = reg_data
            if stage.data2reg:
                reg_data.next = intbv(
                    node_input.a * node_input.b,
                    min=-reg_max,
                    max=reg_max)[1 + NONFRACTION_SIZE + 2 * FRACTION_SIZE:FRACTION_SIZE].signed()
        return instances()
    node.logic = mul
    return node


def add(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return a + b

    node = InnerNode()

    node.add_input(a=a, b=b)
    res = Signal(num.default())
    node.add_output(res)

    @block
    def add(clk, stage, node_input, node_output):
        reg_data = clone_signal(node_output.default)

        @always_seq(clk.posedge, reset=None)
        def drive_data():
            if stage.data2out:
                node_output.default.next = node_input.a + node_input.b
            if stage.reg2out:
                node_output.default.next = reg_data
            if stage.data2reg:
                reg_data.next = node_input.a + node_input.b
        return instances()
    node.logic = add
    return node


def sub(a, b):
    node = InnerNode()

    node.add_input(a=a, b=b)
    res = Signal(num.default())
    node.add_output(res)

    @block
    def sub(clk, stage, node_input, node_output):
        reg_data = clone_signal(node_output.default)

        @always_seq(clk.posedge, reset=None)
        def drive_data():
            if stage.data2out:
                node_output.default.next = node_input.a - node_input.b
            if stage.reg2out:
                node_output.default.next = reg_data
            if stage.data2reg:
                reg_data.next = node_input.a - node_input.b
        return instances()
    node.logic = sub
    return node


def reduce_sum(vec):
    if len(vec) == 0:
        return 0
    elif len(vec) == 1:
        return vec[0]
    else:
        res_vec = vec.copy()
        while len(res_vec) >= 2:
            in_vec = res_vec
            res_vec = []
            while len(in_vec) >= 2:
                res_vec.append(
                    add(in_vec.pop(), in_vec.pop())
                )
            if len(in_vec) == 1:
                res_vec.append(in_vec[0])
        return res_vec[0]


class UnequalVectorLength(Exception):
    pass


def lincomb(vec_a, vec_b):
    if len(vec_a) != len(vec_b):
        raise UnequalVectorLength("len(in_a) = %d != len(in_b) = %d" % (len(vec_a), len(vec_b)))
    n_elements = len(vec_a)

    # Remove elements where one factor is 0
    valid = [
        (isinstance(vec_a[i], SignalType) or vec_a[i] != 0)
        and (isinstance(vec_b[i], SignalType) or vec_b[i] != 0)
        for i in range(n_elements)
    ]
    vec_a = [vec_a[i] for i in range(n_elements) if valid[i]]
    vec_b = [vec_b[i] for i in range(n_elements) if valid[i]]
    n_elements = len(vec_a)

    if n_elements == 0:
        return 0
    elif n_elements == 1:
        return mul(vec_a[0], vec_b[0])
    else:
        partial_results = []
        for i in range(n_elements):
            partial_results.append(mul(vec_a[i], vec_b[i]))
        return reduce_sum(partial_results)

