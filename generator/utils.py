from myhdl import Signal, SignalType

from generator import num


def clone_signal(sig, value=0):
    """
    Clone a single signal.

    :param sig: signal to be cloned
    :param value: reset value of new signal
    :return: new signal
    """
    if sig._type == bool:
        return Signal(bool(value))
    return Signal(num.same_as(sig, val=value))


def clone_signal_structure(sig_data, value=0):
    """
    Clone a signal structure.

    :param sig_data: signal structure to be cloned
    :param value: reset value of new signals
    :return: new signal structure
    """
    if isinstance(sig_data, SignalType):
        return clone_signal(sig_data, value=value)
    elif isinstance(sig_data, list):
        return [clone_signal_structure(sub_sig, value) for sub_sig in sig_data]
    else:
        raise Exception('Can not clone signal data structure.')


def bind(func, *args):
    """
    Bind some arguments to a function.

    :param func: unbinded function
    :param args: arguments to be bind
    :return: binded function
    """
    def _bind(*unbind_args, _args=args):
        return func(*args, *unbind_args)
    return _bind
