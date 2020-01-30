from myhdl import Signal, SignalType

import num


def clone_signal(sig, value=0):
    if sig._type == bool:
        return Signal(bool(value))
    return Signal(num.same_as(sig, val=value))


def clone_signal_structure(sig_data, value=0):
    if isinstance(sig_data, SignalType):
        return clone_signal(sig_data, value=value)
    elif isinstance(sig_data, list):
        return [clone_signal_structure(sub_sig, value) for sub_sig in sig_data]
    else:
        raise Exception('Can not clone signal data structure.')
