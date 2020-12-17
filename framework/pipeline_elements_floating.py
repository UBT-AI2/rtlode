from enum import Enum, auto

from myhdl import block, Signal, instances, always_seq, always_comb, SignalType

from framework.pipeline import PipelineNode, PipeConstant
from framework.fifo import FifoProducer, FifoConsumer, fifo
from utils import num
from utils.num import FloatingPrecission


class NumericFunction(Enum):
    MUL = auto()
    ADD = auto()
    SUB = auto()


_ip_core_infos = {
    NumericFunction.MUL: {
        'analog_function': lambda x, y: x * y,
        FloatingPrecission.SINGLE: {
            'latency': 3,
            'component': 'multfp_single'
        },
        FloatingPrecission.DOUBLE: {
            'latency': 5,
            'component': 'multfp_double'
        }
    },
    NumericFunction.ADD: {
        'analog_function': lambda x, y: x + y,
        FloatingPrecission.SINGLE: {
            'latency': 3,
            'component': 'addfp_single'
        },
        FloatingPrecission.DOUBLE: {
            'latency': 7,
            'component': 'addfp_double'
        }
    },
    NumericFunction.SUB: {
        'analog_function': lambda x, y: x - y,
        FloatingPrecission.SINGLE: {
            'latency': 3,
            'component': 'subfp_single'
        },
        FloatingPrecission.DOUBLE: {
            'latency': 7,
            'component': 'subfp_double'
        }
    },
}


def _get_ip_core_info(function: NumericFunction, num_factory: num.FloatingNumberFactory):
    return _ip_core_infos[function][num_factory.precission]


def _calc_analog(function: NumericFunction, a, b):
    return _ip_core_infos[function]['analog_function'](a, b)


def _handle_inputs(sig, data_width):
    if isinstance(sig, int):
        return "{}'d{}".format(data_width, sig)
    elif isinstance(sig, SignalType):
        sig.read = True
        return sig


@block
def register(clk, rst, previous_signal, next_signal):
    @always_seq(clk.posedge, reset=rst)
    def logic():
        next_signal.next = previous_signal

    return instances()


altfp_inst_counter = 0


@block
def altfp(clk, dataa, datab, result, num_factory: num.FloatingNumberFactory = None, function: NumericFunction = None):
    assert num_factory is not None
    assert function is not None

    ip_core = _get_ip_core_info(function, num_factory)
    component = ip_core['component']

    internal_pipeline = [0 for _ in range(ip_core['latency'] - 1)]

    data_width = num_factory.nbr_bits

    dataa_desc = _handle_inputs(dataa, data_width)
    datab_desc = _handle_inputs(datab, data_width)

    @always_seq(clk.posedge, reset=None)
    def logic():
        if function == NumericFunction.MUL:
            calc_res = num_factory.value_of(dataa) * num_factory.value_of(datab)
        elif function == NumericFunction.ADD:
            calc_res = num_factory.value_of(dataa) + num_factory.value_of(datab)
        elif function == NumericFunction.SUB:
            calc_res = num_factory.value_of(dataa) - num_factory.value_of(datab)
        else:
            raise NotImplementedError

        internal_pipeline.insert(0, num_factory.create_constant(calc_res))
        result.next = internal_pipeline.pop()

    result.driven = 'reg'
    for d in [dataa, datab]:
        if isinstance(d, SignalType):
            d.read = True

    global altfp_inst_counter
    altfp_inst_counter += 1

    return instances()


altfp.verilog_code = \
    """
$component altfp_component_$altfp_inst_counter (
                .clk ($clk),
                .a ($dataa_desc),
                .b ($datab_desc),
                .q ($result));
    """


@block
def altfp_wrapper(
        clk, rst,
        in_stage_valid, in_stage_busy,
        out_stage_valid, out_stage_busy,
        node_input, node_output,
        pipeline_latency=5,
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
    :param pipeline_latency: latency of the altfp pipeline
    :return: myhdl instances
    """
    assert pipeline_latency > 0

    num_factory = num.get_numeric_factory()

    inner_pipe_res = Signal(num_factory.create())
    inner_pipe = altfp(
        clk, node_input.a, node_input.b, inner_pipe_res, **kwargs
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


def generic(function: NumericFunction, a, b):
    # TODO docstring

    num_factory = num.get_numeric_factory()
    assert isinstance(num_factory, num.FloatingNumberFactory)

    if isinstance(a, PipeConstant) and isinstance(b, PipeConstant):
        return PipeConstant.from_float(
            _calc_analog(function, num_factory.value_of(a.get_value()), num_factory.value_of(b.get_value()))
        )
    elif isinstance(a, PipeConstant) or isinstance(b, PipeConstant):
        if isinstance(a, PipeConstant):
            static_value = a.get_value()
            dynamic_value = b
        else:
            static_value = b.get_value()
            dynamic_value = a

        # function dependent optimation
        if function == NumericFunction.MUL:
            if static_value == 0:
                return PipeConstant.from_float(0)
            elif static_value == 1:
                return dynamic_value
        elif function == NumericFunction.ADD or function == NumericFunction.SUB:
            if static_value == 0:
                return dynamic_value

    latency = _get_ip_core_info(function, num_factory)['latency']

    node = PipelineNode(latency + 1)

    node.add_inputs(a=a, b=b)
    res = Signal(num_factory.create())
    node.add_output(res)
    node.set_name(function.name.lower())

    node.set_logic(
        altfp_wrapper,
        pipeline_latency=latency,
        num_factory=num_factory,
        function=function
    )
    return node


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
    return generic(NumericFunction.MUL, a, b)


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
    return generic(NumericFunction.ADD, a, b)


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
    return generic(NumericFunction.SUB, a, b)


def negate(val):
    """
    Pipeline node which negates the given parameter.
    The return type is int if the type of the parameter is also int.
    Otherwise a SeqNode is returned.
    :param val: parameter val
    :return: int or pipeline node
    """
    return val * PipeConstant.from_float(-1.0)
