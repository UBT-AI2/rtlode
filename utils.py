from myhdl import Signal, ResetSignal, SignalType, block, always_comb

import num


class FlowControl:
    def __init__(self, clk: SignalType, rst: ResetSignal, enb: SignalType, fin: SignalType):
        self.clk = clk
        self.rst = rst
        self.enb = enb
        self.fin = fin

    def clk_edge(self):
        return self.clk.posedge

    def create_subflow(self, enb=None, fin=None):
        if enb is None:
            enb = Signal(bool(0))
        if fin is None:
            fin = Signal(bool(0))
        return FlowControl(self.clk, self.rst, enb, fin)


class Pipeline:
    def __init__(self, flow: FlowControl):
        self._flow = flow
        self._components = []

    @block
    def create(self):
        insts = []
        pre_fin = self._flow.enb
        for (mod, args) in self._components:
            subflow = self._flow.create_subflow(enb=pre_fin)
            pre_fin = subflow.fin
            insts.append(mod(*args, flow=subflow))

        @always_comb
        def assign():
            self._flow.fin.next = pre_fin

        return insts + [assign]

    def append(self, mod, *args):
        self._components.append((mod, args))
        return self


def clone_signal(sig, value=0):
    return Signal(num.same_as(sig, val=value))


def clone_signal_structure(sig_data, value=0):
    if isinstance(sig_data, SignalType):
        return Signal(num.same_as(sig_data, val=value))
    elif isinstance(sig_data, list):
        return [clone_signal_structure(sub_sig, value) for sub_sig in sig_data]
    else:
        raise Exception('Can not clone signal data structure.')
