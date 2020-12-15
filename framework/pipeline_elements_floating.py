from myhdl import block, Signal, instances, always_seq, always_comb, SignalType

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
def altfp_wrapper(
        clk, rst,
        in_stage_valid, in_stage_busy,
        out_stage_valid, out_stage_busy,
        node_input, node_output,
        pipeline=None, pipeline_latency=5,
        **kwargs):
    """
    Wrapper functio for altfp instances.
    Implements additional logic to track value validity and proper handling while pipeline stalls.

    :param clk: clock signal
    :param rst: reset signal
    :param in_stage_valid: is input currently valid?
    :param in_stage_busy: is input stage currently signaling that it is busy?
    :param out_stage_valid: is output currently valid?
    :param out_stage_busy: is output stage currently signaling that it is busy?
    :param node_input: input values of the node
    :param node_output: output values of the node
    :param pipeline: altfp function
    :param pipeline_latency: latency of the altfp pipeline
    :return: myhdl instances
    """
    assert pipeline_latency > 0

    num_factory = num.get_numeric_factory()

    inner_pipe_res = Signal(num_factory.create())
    inner_pipe = pipeline(
        clk, node_input.a, node_input.b, inner_pipe_res, pipeline_latency=pipeline_latency, **kwargs
    )

    in_valid = Signal(num.get_bool_factory().create())

    @always_seq(clk.posedge, reset=rst)
    def check_input_validity():
        in_valid.next = in_stage_valid and not in_stage_busy

    valid_signals = [Signal(num.get_bool_factory().create()) for _ in range(pipeline_latency - 1)]
    valid_reg = []

    previous_signal = in_valid
    for next_signal in valid_signals:
        valid_reg.append(
            register(clk, rst, previous_signal, next_signal)
        )
        previous_signal = next_signal
    valid = previous_signal

    # Must be a fifo of size pipeline_latency
    reg_fifo_p = FifoProducer(Signal(num_factory.create()))
    reg_fifo_c = FifoConsumer(Signal(num_factory.create()))
    bits_needed = len("{0:b}".format(pipeline_latency + 1)) + 1
    reg_fifo = fifo(clk, rst, reg_fifo_p, reg_fifo_c, buffer_size_bits=bits_needed)

    reg_fill_level = Signal(num.get_integer_factory().create(0))

    @always_seq(clk.posedge, reset=rst)
    def drive_data():
        reg_fifo_p.wr.next = False
        if not out_stage_busy:
            if reg_fifo_c.empty:
                node_output.default.next = inner_pipe_res
            else:
                node_output.default.next = reg_fifo_c.data
                reg_fill_level.next = reg_fill_level - 1

        if valid and ((out_stage_valid and out_stage_busy) or not reg_fifo_c.empty):
            reg_fifo_p.data.next = inner_pipe_res
            reg_fifo_p.wr.next = True
            reg_fill_level.next = reg_fill_level + 1

    @always_comb
    def drive_fifo_c():
        reg_fifo_c.rd.next = not out_stage_busy

    return instances()


@block
def mul_altfp(clk, dataa, datab, result, pipeline_latency=5, width_exp=11, width_man=52):
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
    for d in [dataa, datab]:
        if isinstance(d, SignalType):
            d.read = True

    return instances()


mul_altfp.verilog_code = \
    """
altfp_mult  altfp_mult_component_$inst (
                .clock ($clk),
                .dataa ($dataa),
                .datab ($datab),
                .result ($result));
    defparam
        altfp_mult_component.denormal_support = "NO",
        altfp_mult_component.lpm_type = "altfp_mult",
        altfp_mult_component.reduced_functionality = "NO",
        altfp_mult_component.pipeline = $pipeline_latency,
        altfp_mult_component.width_exp = $width_exp,
        altfp_mult_component.width_man = $width_man;
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
    inner_latency = 5

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

    node = PipelineNode(inner_latency + 1)

    node.add_inputs(a=a, b=b)
    res = Signal(num_factory.create())
    node.add_output(res)
    node.set_name('mul')

    node.set_logic(
        altfp_wrapper,
        pipeline_latency=inner_latency,
        pipeline=mul_altfp,
        width_exp=num_factory.width_exp,
        width_man=num_factory.width_man
    )
    return node


@block
def add_sub_altfp(clk, dataa, datab, result, pipeline_latency=7, direction='ADD', width_exp=11, width_man=52):
    num_factory = num.get_numeric_factory()

    internal_pipeline = [0 for _ in range(pipeline_latency - 1)]

    @always_seq(clk.posedge, reset=None)
    def logic():
        internal_pipeline.insert(
            0,
            num_factory.create_constant(
                num_factory.value_of(dataa) + num_factory.value_of(datab) if direction == 'ADD' else
                num_factory.value_of(dataa) - num_factory.value_of(datab)
            )
        )
        result.next = internal_pipeline.pop()

    result.driven = 'reg'
    for d in [dataa, datab]:
        if isinstance(d, SignalType):
            d.read = True

    return instances()


add_sub_altfp.verilog_code = \
    """
altfp_add_sub   altfp_add_sub_component_$inst (
                .clock ($clk),
                .dataa ($dataa),
                .datab ($datab),
                .result ($result));
    defparam
        altfp_mult_component.denormal_support = "NO",
        altfp_mult_component.lpm_type = "altfp_add_sub",
        altfp_mult_component.reduced_functionality = "NO",
        altfp_mult_component.direction = "$direction",
        altfp_mult_component.rounding = "TO_NEAREST",
        altfp_mult_component.pipeline = $pipeline_latency,
        altfp_mult_component.width_exp = $width_exp,
        altfp_mult_component.width_man = $width_man;
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

    node.set_logic(
        altfp_wrapper,
        pipeline_latency=inner_latency,
        pipeline=add_sub_altfp,
        width_exp=num_factory.width_exp,
        width_man=num_factory.width_man
    )
    return node


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

    node.set_logic(
        altfp_wrapper,
        pipeline_latency=inner_latency,
        pipeline=add_sub_altfp,
        width_exp=num_factory.width_exp,
        width_man=num_factory.width_man,
        direction='SUB'
    )
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
