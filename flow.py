from dataclasses import dataclass

from myhdl import SignalType, ResetSignal, Signal


@dataclass
class FlowControl:
    clk: SignalType
    rst: ResetSignal
    enb: SignalType
    fin: SignalType

    def clk_edge(self):
        return self.clk.posedge

    def create_subflow(self, rst=None, enb=None, fin=None):
        if rst is None:
            rst = self.rst
        if enb is None:
            enb = Signal(bool(0))
        if fin is None:
            fin = Signal(bool(0))
        return FlowControl(self.clk, rst, enb, fin)
