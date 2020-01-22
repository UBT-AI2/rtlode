from myhdl import Signal, ResetSignal, SignalType

import num


class FlowControl:
    def __init__(self, clk: SignalType, rst: ResetSignal, enb: SignalType, fin: SignalType):
        self.clk = clk
        self.rst = rst
        self.enb = enb
        self.fin = fin


def clone_signal(sig, value=0):
    return Signal(num.same_as(sig, val=value))


def clone_signal_structure(sig_data, value=0):
    if isinstance(sig_data, SignalType):
        return Signal(num.same_as(sig_data, val=value))
    elif isinstance(sig_data, list):
        return [clone_signal_structure(sub_sig, value) for sub_sig in sig_data]
    else:
        raise Exception('Can not clone signal data structure.')
