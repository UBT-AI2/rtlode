from enum import Enum, auto

from myhdl import block, Signal, instances, always_seq, always_comb, SignalType

from framework.pipeline import MultipleCycleNode, PipeConstant, PipeNumeric, PipeSignal
from framework.fifo import FifoProducer, FifoConsumer, fifo
from utils import num
from utils.num import FloatingPrecision


class NumericFunction(Enum):
    MUL = auto()
    ADD = auto()
    SUB = auto()


_ip_core_infos = {
    NumericFunction.MUL: {
        'analog_function': lambda x, y: x * y,
        FloatingPrecision.SINGLE: {
            'latency': 3,
            'component': 'multfp_single'
        },
        FloatingPrecision.DOUBLE: {
            'latency': 5,
            'component': 'multfp_double'
        }
    },
    NumericFunction.ADD: {
        'analog_function': lambda x, y: x + y,
        FloatingPrecision.SINGLE: {
            'latency': 3,
            'component': 'addfp_single'
        },
        FloatingPrecision.DOUBLE: {
            'latency': 7,
            'component': 'addfp_double'
        }
    },
    NumericFunction.SUB: {
        'analog_function': lambda x, y: x - y,
        FloatingPrecision.SINGLE: {
            'latency': 3,
            'component': 'subfp_single'
        },
        FloatingPrecision.DOUBLE: {
            'latency': 7,
            'component': 'subfp_double'
        }
    },
}


def _get_ip_core_info(function: NumericFunction, num_factory: num.FloatingNumberType):
    return _ip_core_infos[function][num_factory.precision]


def _calc_analog(function: NumericFunction, a, b):
    return _ip_core_infos[function]['analog_function'](a, b)


def _handle_inputs(sig, data_width):
    if isinstance(sig, int):
        return "{}'d{}".format(data_width, sig)
    elif isinstance(sig, SignalType):
        sig.read = True
        return sig


@block
def stupid_register(clk, rst, previous_signal, next_signal):
    @always_seq(clk.posedge, reset=rst)
    def logic():
        next_signal.next = previous_signal

    return instances()


# Global counter needed to provide unique instance names
fp_core_inst_counter = 0


@block
def fp_core(clk, dataa, datab, result, num_factory: num.FloatingNumberType = None, function: NumericFunction = None):
    """
    Implementing a floating point ip core instance.
    Ip Core must be described in _ip_core_info. Analog myhdl simulation logic is implemented.
    :param clk: clock signal
    :param dataa: parameter a
    :param datab: parameter b
    :param result: result signal
    :param num_factory: NumberFactory to be used
    :param function: NumericFunction to implement
    :return: myhdl instances
    """
    assert num_factory is not None and function is not None

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

    global fp_core_inst_counter
    fp_core_inst_counter += 1

    return instances()


fp_core.verilog_code = \
    """
$component fp_core_component_$fp_core_inst_counter (
                .clk ($clk),
                .a ($dataa_desc),
                .b ($datab_desc),
                .q ($result));
    """


def generic(function: NumericFunction, a: PipeNumeric, b: PipeNumeric):
    """
    Pipeline node which is able to apply the given NumericFunction to the two parameters (a, b).
    Optimization is performed where possible.
    The return type is PipeConstant if both parameters were integer and so the result is static.
    In other cases the return type is defined by the used ip core - usually MultipleCycleNode.
    :param function: NumericFunction to be applied
    :param a: parameter a
    :param b: parameter b
    :return: PipeConstant for static results or pipeline node
    """
    assert a.get_type() == b.get_type()
    num_type = num.get_default_type()
    assert isinstance(num_type, num.FloatingNumberType)

    if isinstance(a, PipeConstant) and isinstance(b, PipeConstant):
        return PipeConstant.from_float(
            _calc_analog(function, num_type.value_of(a.get_value()), num_type.value_of(b.get_value()))
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

    latency = _get_ip_core_info(function, num_type)['latency']

    node = MultipleCycleNode(latency + 1)

    node.add_inputs(a=a, b=b)
    res = PipeSignal(num_type, Signal(num_type.create()))
    node.add_output(res)
    node.set_name('floating-{}'.format(function.name.lower()))

    node.set_logic(
        fp_core,
        num_factory=num_type,
        function=function
    )
    return node


def mul(a, b):
    """
    Pipeline node which multiplies the two given parameters.
    Optimization is performed where possible.
    The return type is PipeConstant if both parameters were integer and so the result is static.
    In other cases the return type is defined by the used ip core - usually MultipleCycleNode.
    :param a: parameter a
    :param b: parameter b
    :return: PipeConstant for static results or pipeline node
    """
    return generic(NumericFunction.MUL, a, b)


def add(a, b):
    """
    Pipeline node which adds the two given parameters.
    Optimization is performed where possible.
    The return type is PipeConstant if both parameters were integer and so the result is static.
    In other cases the return type is defined by the used ip core - usually MultipleCycleNode.
    :param a: parameter a
    :param b: parameter b
    :return: PipeConstant for static results or pipeline node
    """
    return generic(NumericFunction.ADD, a, b)


def sub(a, b):
    """
    Pipeline node which substracts b from a.
    Optimization is performed where possible.
    The return type is PipeConstant if both parameters were integer and so the result is static.
    In other cases the return type is defined by the used ip core - usually MultipleCycleNode.
    :param a: parameter a
    :param b: parameter b
    :return: PipeConstant for static results or pipeline node
    """
    return generic(NumericFunction.SUB, a, b)


def negate(val):
    """
    Pipeline function which negates the given parameter by multiplying it with -1.\
    :param val: parameter val
    :return: PipeConstant for static results or pipeline node
    """
    return val * PipeConstant.from_float(-1.0)
