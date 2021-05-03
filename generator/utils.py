from myhdl import Signal, SignalType, block, always_seq, modbv, intbv, always_comb


@block
def reinterpret_as_signed(data_in, data_out):
    @always_comb
    def _assign():
        data_out.next = data_in.signed()

    return _assign


def clone_signal(sig, reset_value=0):
    """
    Clone a single signal.

    :param sig: signal to be cloned
    :param reset_value: reset value of new signal
    :return: new signal
    """
    if sig._type == bool:
        return Signal(bool(reset_value))

    if isinstance(sig.val, modbv):
        value = modbv(reset_value, min=sig.min, max=sig.max)
    elif isinstance(sig.val, intbv):
        value = intbv(reset_value, min=sig.min, max=sig.max)
    else:
        raise NotImplemented()

    return Signal(value)


def clone_signal_structure(sig_data, value=0):
    """
    Clone a signal structure.

    :param sig_data: signal structure to be cloned
    :param value: reset value of new signals
    :return: new signal structure
    """
    if isinstance(sig_data, SignalType):
        return clone_signal(sig_data, reset_value=value)
    elif isinstance(sig_data, list):
        return [clone_signal_structure(sub_sig, value) for sub_sig in sig_data]
    else:
        raise Exception('Can not clone signal data structure.')


"""
No easy way to implement these assigns smarter because of limitations of the myhdl conversion.
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
