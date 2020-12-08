from myhdl import block, Signal, instances, always_seq, always_comb

from framework.pipeline import PipelineNode, PipeConstant
from framework.fifo import FifoProducer, FifoConsumer, fifo
from utils import num


@block
def register(clk, rst, previous_signal, next_signal):

    @always_seq(clk.posedge, reset=rst)
    def logic():
        next_signal.next = previous_signal

    return instances()


@block
def mul_wrapper(clk, rst, in_stage_valid, in_stage_busy, out_stage, out_busy, node_input, node_output, inner_pipeline=None, inner_latency=5):
    num_factory = num.get_numeric_factory()

    inner_pipe_res = Signal(num_factory.create())
    inner_pipe = inner_pipeline(clk, node_input.a, node_input.b, inner_pipe_res, pipeline_latency=inner_latency)

    in_valid = Signal(num.get_bool_factory().create())

    @always_seq(clk.posedge, reset=rst)
    def check_input_validity():
        in_valid.next = in_stage_valid and not in_stage_busy

    valid_signals = [Signal(num.get_bool_factory().create()) for _ in range(inner_latency - 1)]
    valid_reg = []

    previous_signal = in_valid
    for next_signal in valid_signals:
        valid_reg.append(
            register(clk, rst, previous_signal, next_signal)
        )
        previous_signal = next_signal
    valid = previous_signal

    # Must be a fifo of size inner_latency
    reg_fifo_p = FifoProducer(Signal(num_factory.create()))
    reg_fifo_c = FifoConsumer(Signal(num_factory.create()))
    reg_fifo = fifo(clk, rst, reg_fifo_p, reg_fifo_c, buffer_size_bits=4)  # TODO

    reg_fill_level = Signal(num.get_integer_factory().create(0))

    @always_seq(clk.posedge, reset=rst)
    def drive_data():
        reg_fifo_p.wr.next = False
        if not out_busy:
            if reg_fifo_c.empty:
                node_output.default.next = inner_pipe_res
            else:
                node_output.default.next = reg_fifo_c.data
                reg_fill_level.next = reg_fill_level - 1

        if valid and ((out_stage.valid and out_busy) or not reg_fifo_c.empty):
            reg_fifo_p.data.next = inner_pipe_res
            reg_fifo_p.wr.next = True
            reg_fill_level.next = reg_fill_level + 1

    @always_comb
    def drive_fifo_c():
        reg_fifo_c.rd.next = not out_busy

    return instances()


@block
def mul_altfp_double(clk, dataa, datab, result, pipeline_latency=5):
    num_factory = num.get_numeric_factory()

    internal_pipeline = [0 for _ in range(pipeline_latency - 1)]

    @always_seq(clk.posedge, reset=None)
    def logic():
        internal_pipeline.insert(
            0,
            num_factory.create_constant(
                num_factory.value_of(dataa) * num_factory.value_of(datab)
            )
        )
        result.next = internal_pipeline.pop()

    result.driven = 'reg'

    return instances()


mul_altfp_double.verilog_code = \
    """
altfp_mult	altfp_mult_component (
                .clock ($clk),
                .dataa ($dataa),
                .datab ($datab),
                .result ($result));
    defparam
        altfp_mult_component.denormal_support = "NO",
        altfp_mult_component.lpm_type = "altfp_mult",
        altfp_mult_component.reduced_functionality = "NO",
        altfp_mult_component.pipeline = $pipeline_latency,
        altfp_mult_component.width_exp = 11,
        altfp_mult_component.width_man = 52;
    """


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
        return PipeConstant.from_float(
            num_factory.value_of(a.get_value()) * num_factory.value_of(b.get_value())
        )
    elif isinstance(a, PipeConstant) or isinstance(b, PipeConstant):
        if isinstance(a, PipeConstant):
            static_value = a.get_value()
            dynamic_value = b
        else:
            static_value = b.get_value()
            dynamic_value = a

        if static_value == 0:
            return PipeConstant.from_float(0)
        elif static_value == 1:
            return dynamic_value

    node = PipelineNode(6)

    node.add_inputs(a=a, b=b)
    res = Signal(num_factory.create())
    node.add_output(res)
    node.set_name('mul')

    node.set_logic(mul_wrapper, inner_latency=5, inner_pipeline=mul_altfp_double)
    return node


@block
def add_altfp_double(clk, dataa, datab, result, pipeline_latency=5):
    num_factory = num.get_numeric_factory()

    internal_pipeline = [0 for _ in range(pipeline_latency - 1)]

    @always_seq(clk.posedge, reset=None)
    def logic():
        internal_pipeline.insert(
            0,
            num_factory.create_constant(
                num_factory.value_of(dataa) + num_factory.value_of(datab)
            )
        )
        result.next = internal_pipeline.pop()

    result.driven = 'reg'

    return instances()


add_altfp_double.verilog_code = \
    """
altfp_add_sub	altfp_add_sub_component (
                .clock ($clk),
                .dataa ($dataa),
                .datab ($datab),
                .result ($result));
    defparam
        altfp_mult_component.denormal_support = "NO",
        altfp_mult_component.lpm_type = "altfp_add_sub",
        altfp_mult_component.reduced_functionality = "NO",
        altfp_mult_component.direction = "ADD",
        altfp_mult_component.rounding = "TO_NEAREST",
        altfp_mult_component.pipeline = $pipeline_latency,
        altfp_mult_component.width_exp = 11,
        altfp_mult_component.width_man = 52;
    """


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
    inner_latency = 7

    num_factory = num.get_numeric_factory()
    if isinstance(a, PipeConstant) and isinstance(b, PipeConstant):
        return PipeConstant.from_float(
            num_factory.value_of(a.get_value()) + num_factory.value_of(b.get_value())
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

    node = PipelineNode(inner_latency + 1)

    node.add_inputs(a=a, b=b)
    res = Signal(num_factory.create())
    node.add_output(res)
    node.set_name('add')

    node.set_logic(mul_wrapper, inner_latency=inner_latency, inner_pipeline=add_altfp_double)
    return node


@block
def sub_altfp_double(clk, dataa, datab, result, pipeline_latency=5):
    num_factory = num.get_numeric_factory()

    internal_pipeline = [0 for _ in range(pipeline_latency - 1)]

    @always_seq(clk.posedge, reset=None)
    def logic():
        internal_pipeline.insert(
            0,
            num_factory.create_constant(
                num_factory.value_of(dataa) - num_factory.value_of(datab)
            )
        )
        result.next = internal_pipeline.pop()

    result.driven = 'reg'

    return instances()


sub_altfp_double.verilog_code = \
    """
altfp_add_sub	altfp_add_sub_component (
                .clock ($clk),
                .dataa ($dataa),
                .datab ($datab),
                .result ($result));
    defparam
        altfp_mult_component.denormal_support = "NO",
        altfp_mult_component.lpm_type = "altfp_add_sub",
        altfp_mult_component.reduced_functionality = "NO",
        altfp_mult_component.direction = "SUB",
        altfp_mult_component.rounding = "TO_NEAREST",
        altfp_mult_component.pipeline = $pipeline_latency,
        altfp_mult_component.width_exp = 11,
        altfp_mult_component.width_man = 52;
    """


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
    inner_latency = 7

    num_factory = num.get_numeric_factory()
    if isinstance(a, PipeConstant) and isinstance(b, PipeConstant):
        return PipeConstant.from_float(
            num_factory.value_of(a.get_value()) - num_factory.value_of(b.get_value())
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

    node = PipelineNode(inner_latency + 1)

    node.add_inputs(a=a, b=b)
    res = Signal(num_factory.create())
    node.add_output(res)
    node.set_name('sub')

    node.set_logic(mul_wrapper, inner_latency=inner_latency, inner_pipeline=sub_altfp_double)
    return node


def negate(val):
    """
    Pipeline node which negates the given parameter.
    The return type is int if the type of the parameter is also int.
    Otherwise a SeqNode is returned.
    :param val: parameter val
    :return: int or pipeline node
    """
    return val * PipeConstant.from_float(-1.0)
