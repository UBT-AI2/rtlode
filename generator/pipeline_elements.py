from myhdl import Signal, block, always_seq, instances, SignalType, intbv, always_comb

from generator.pipeline import SeqNode, CombNode
from generator.utils import clone_signal
from utils import num
from utils.num import FRACTION_SIZE, NONFRACTION_SIZE


@block
def mul_by_shift_left(node_input, node_output):
    @always_comb
    def shift_left():
        node_output.default.next = node_input.value << node_input.shift_by

    return shift_left


@block
def mul_by_shift_right(node_input, node_output):
    @always_comb
    def shift_right():
        node_output.default.next = node_input.value >> node_input.shift_by

    return shift_right


@block
def mul_dsp_c(clk, stage, node_input, node_output):
    reg_max = 2 ** (NONFRACTION_SIZE + 2 * FRACTION_SIZE)
    reg_data = clone_signal(node_output.default)

    @always_seq(clk.posedge, reset=None)
    def drive_data():
        if stage.data2out:
            node_output.default.next = intbv(
                intbv(node_input.static_value).signed() * node_input.dynamic_value,
                min=-reg_max,
                max=reg_max)[1 + NONFRACTION_SIZE + 2 * FRACTION_SIZE:FRACTION_SIZE].signed()
        if stage.reg2out:
            node_output.default.next = reg_data
        if stage.data2reg:
            reg_data.next = intbv(
                intbv(node_input.static_value).signed() * node_input.dynamic_value,
                min=-reg_max,
                max=reg_max)[1 + NONFRACTION_SIZE + 2 * FRACTION_SIZE:FRACTION_SIZE].signed()

    return instances()


@block
def mul_dsp(clk, stage, node_input, node_output):
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


def mul(a, b):
    """
    Pipeline node which multiplies the two given parameters.
    Optimization is performed where possible.
    The return type is int if both parameters were integer and so the result is static. Depending of the multiplication
    implementation used the return type is CombNode or SeqNode in other cases.
    :param a: parameter a
    :param b: parameter b
    :return: int or pipeline node
    """
    if isinstance(a, int) and isinstance(b, int):
        reg_max = 2 ** (NONFRACTION_SIZE + 2 * FRACTION_SIZE)
        return int(intbv(
                        num.default(a) * num.default(b),
                        min=-reg_max,
                        max=reg_max)[1 + NONFRACTION_SIZE + 2 * FRACTION_SIZE:FRACTION_SIZE].signed())
    elif isinstance(a, int) or isinstance(b, int):
        if isinstance(a, int):
            static_value = a
            dynamic_value = b
        else:
            static_value = b
            dynamic_value = a

        if static_value == 0:
            return 0
        elif bin(static_value).count('1') == 1:
            # This multiplication can be implemented ny shifts.
            bin_repr = bin(static_value)
            shift_by = len(bin_repr) - 1 - bin_repr.index('1') - FRACTION_SIZE
            print('Implemented multiplication as shift by: ', shift_by)
            if shift_by == 0:
                # Just return the dynamic_value
                return dynamic_value

            node = CombNode()
            node.add_input(value=dynamic_value)
            res = Signal(num.default())
            node.add_output(res)
            node.set_name('mul_by_shift')

            if shift_by > 0:
                node.add_input(shift_by=shift_by)

                node.set_logic(mul_by_shift_left)
            elif shift_by < 0:
                shift_by = -shift_by
                node.add_input(shift_by=shift_by)

                node.set_logic(mul_by_shift_right)
            return node
        else:
            node = SeqNode()

            node.add_input(dynamic_value=dynamic_value, static_value=static_value)
            res = Signal(num.default())
            node.add_output(res)
            node.set_name('mul')

            node.set_logic(mul_dsp_c)
            return node
    else:
        node = SeqNode()

        node.add_input(a=a, b=b)
        res = Signal(num.default())
        node.add_output(res)
        node.set_name('mul')

        node.set_logic(mul_dsp)
        return node


@block
def add_seq(clk, stage, node_input, node_output):
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


def add(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return a + b

    node = SeqNode()

    node.add_input(a=a, b=b)
    res = Signal(num.default())
    node.add_output(res)
    node.set_name('add')
    node.set_logic(add_seq)

    return node


@block
def sub_seq(clk, stage, node_input, node_output):
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


def sub(a, b):
    node = SeqNode()

    node.add_input(a=a, b=b)
    res = Signal(num.default())
    node.add_output(res)
    node.set_name('sub')
    node.set_logic(sub_seq)

    return node


@block
def negate_seq(clk, stage, node_input, node_output):
    reg_data = clone_signal(node_output.default)

    @always_seq(clk.posedge, reset=None)
    def drive_data():
        if stage.data2out:
            node_output.default.next = -node_input.val
        if stage.reg2out:
            node_output.default.next = reg_data
        if stage.data2reg:
            reg_data.next = -node_input.val
    return instances()


def negate(val):
    node = SeqNode()

    node.add_input(val=val)
    res = Signal(num.default())
    node.add_output(res)
    node.set_name('negate')
    node.set_logic(negate_seq)

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


def vec_mul(vec_a, vec_b):
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

