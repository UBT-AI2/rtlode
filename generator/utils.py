from myhdl import Signal, SignalType, block, always_seq

from utils import num


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


"""
No easy eay to implement these assigns smarter because of limitations of the myhdl conversion.
Each signal can only be driven by one instance.
"""


@block
def assign(clk, condition, in_val, out_val):
    @always_seq(clk.posedge, reset=None)
    def _assign():
        if condition:
            out_val.next = in_val
    return _assign


@block
def assign_2(clk, condition_1, in_val_1, condition_2, in_val_2, out_val):
    @always_seq(clk.posedge, reset=None)
    def _assign():
        if condition_1:
            out_val.next = in_val_1
        if condition_2:
            out_val.next = in_val_2
    return _assign


@block
def assign_3(clk, condition_1, in_val_1, condition_2, in_val_2, condition_3, in_val_3, out_val):
    @always_seq(clk.posedge, reset=None)
    def _assign():
        if condition_1:
            out_val.next = in_val_1
        if condition_2:
            out_val.next = in_val_2
        if condition_3:
            out_val.next = in_val_3
    return _assign
