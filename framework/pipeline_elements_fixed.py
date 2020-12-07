from myhdl import Signal, block, always_seq, instances, intbv, always_comb

from framework.pipeline import SeqNode, CombNode, PipeConstant
from generator.utils import clone_signal
from utils import num


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
def mul_dsp_c(clk, rst, stage, node_input, node_output):
    num_factory = num.get_numeric_factory()
    reg_max = 2 ** (num_factory.nonfraction_bits + 2 * num_factory.fraction_bits)
    out = Signal(intbv(0, min=-reg_max, max=reg_max))
    reg_data = clone_signal(out)

    @always_seq(clk.posedge, reset=None)
    def drive_data():
        if stage.data2out:
            out.next = intbv(node_input.static_value).signed() * node_input.dynamic_value
        if stage.reg2out:
            out.next = reg_data
        if stage.data2reg:
            reg_data.next = intbv(node_input.static_value).signed() * node_input.dynamic_value

    @always_comb
    def resize():
        node_output.default.next = \
            out[1 + num_factory.nonfraction_bits + 2 * num_factory.fraction_bits:num_factory.fraction_bits].signed()

    return instances()


@block
def mul_dsp(clk, rst, stage, node_input, node_output):
    num_factory = num.get_numeric_factory()
    reg_max = 2 ** (num_factory.nonfraction_bits + 2 * num_factory.fraction_bits)
    out = Signal(intbv(0, min=-reg_max, max=reg_max))
    reg_data = clone_signal(out)

    @always_seq(clk.posedge, reset=None)
    def drive_data():
        if stage.data2out:
            out.next = node_input.a * node_input.b
        if stage.reg2out:
            out.next = reg_data
        if stage.data2reg:
            reg_data.next = node_input.a * node_input.b

    @always_comb
    def resize():
        node_output.default.next = \
            out[1 + num_factory.nonfraction_bits + 2 * num_factory.fraction_bits:num_factory.fraction_bits].signed()

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
    num_factory = num.get_numeric_factory()
    if isinstance(a, PipeConstant) and isinstance(b, PipeConstant):
        reg_max = 2 ** (num_factory.nonfraction_bits + 2 * num_factory.fraction_bits)
        return PipeConstant(int(intbv(
            num_factory.create_constant(a.get_value()) * num_factory.create_constant(b.get_value()),
            min=-reg_max,
            max=reg_max
        )[1 + num_factory.nonfraction_bits + 2 * num_factory.fraction_bits:num_factory.fraction_bits].signed()))
    elif isinstance(a, PipeConstant) or isinstance(b, PipeConstant):
        if isinstance(a, PipeConstant):
            static_value = a.get_value()
            dynamic_value = b
        else:
            static_value = b.get_value()
            dynamic_value = a

        if static_value == 0:
            return PipeConstant.from_float(0)
        elif bin(static_value).count('1') == 1:
            # This multiplication can be implemented ny shifts.
            bin_repr = bin(static_value)
            shift_by = len(bin_repr) - 1 - bin_repr.index('1') - num_factory.fraction_bits
            print('Implemented multiplication as shift by: ', shift_by)
            if shift_by == 0:
                # Just return the dynamic_value
                return dynamic_value

            node = CombNode()
            node.add_inputs(value=dynamic_value)
            res = Signal(num_factory.create())
            node.add_output(res)
            node.set_name('mul_by_shift')

            if shift_by > 0:
                node.add_inputs(shift_by=shift_by)

                node.set_logic(mul_by_shift_left)
            elif shift_by < 0:
                shift_by = -shift_by
                node.add_inputs(shift_by=shift_by)

                node.set_logic(mul_by_shift_right)
            return node
        else:
            node = SeqNode()

            node.add_inputs(dynamic_value=dynamic_value, static_value=static_value)
            res = Signal(num_factory.create())
            node.add_output(res)
            node.set_name('mul')

            node.set_logic(mul_dsp_c)
            return node
    else:
        node = SeqNode()

        node.add_inputs(a=a, b=b)
        res = Signal(num_factory.create())
        node.add_output(res)
        node.set_name('mul')

        node.set_logic(mul_dsp)
        return node


@block
def add_seq(clk, rst, stage, node_input, node_output):
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
    """
    Pipeline node which adds the two given parameters.
    Optimization is performed where possible.
    The return type is int if both parameters were integer and so the result is static.
    Otherwise a SeqNode is returned.
    :param a: parameter a
    :param b: parameter b
    :return: int or pipeline node
    """
    num_factory = num.get_numeric_factory()
    if isinstance(a, PipeConstant) and isinstance(b, PipeConstant):
        return PipeConstant(
            int(
                num_factory.create_from_constant(a.get_value()) + num_factory.create_from_constant(b.get_value())
            )
        )
    elif isinstance(a, PipeConstant) or isinstance(b, PipeConstant):
        if isinstance(a, PipeConstant):
            static_value = a.get_value()
            dynamic_value = b
        else:
            static_value = b.get_value()
            dynamic_value = a

        if static_value == 0:
            return dynamic_value

    node = SeqNode()

    node.add_inputs(a=a, b=b)
    res = Signal(num_factory.create())
    node.add_output(res)
    node.set_name('add')
    node.set_logic(add_seq)

    return node


@block
def sub_seq(clk, rst, stage, node_input, node_output):
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
    """
    Pipeline node which substracts b from a.
    Optimization is performed where possible.
    The return type is int if both parameters were integer and so the result is static.
    Otherwise a SeqNode is returned.
    :param a: parameter a
    :param b: parameter b
    :return: int or pipeline node
    """
    num_factory = num.get_numeric_factory()
    if isinstance(a, PipeConstant) and isinstance(b, PipeConstant):
        return PipeConstant(
            int(
                num_factory.create_from_constant(a.get_value()) - num_factory.create_from_constant(b.get_value())
            )
        )
    elif isinstance(a, PipeConstant) or isinstance(b, PipeConstant):
        if isinstance(a, PipeConstant):
            static_value = a.get_value()
            dynamic_value = b
        else:
            static_value = b.get_value()
            dynamic_value = a

        if static_value == 0:
            return dynamic_value

    node = SeqNode()

    node.add_inputs(a=a, b=b)
    res = Signal(num_factory.create())
    node.add_output(res)
    node.set_name('sub')
    node.set_logic(sub_seq)

    return node


@block
def negate_seq(clk, rst, stage, node_input, node_output):
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
    """
    Pipeline node which negates the given parameter.
    The return type is int if the type of the parameter is also int.
    Otherwise a SeqNode is returned.
    :param val: parameter val
    :return: int or pipeline node
    """
    if isinstance(val, PipeConstant):
        return PipeConstant(-val.get_value())

    node = SeqNode()

    node.add_inputs(val=val)
    res = Signal(num.get_numeric_factory().create())
    node.add_output(res)
    node.set_name('negate')
    node.set_logic(negate_seq)

    return node
