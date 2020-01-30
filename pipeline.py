from myhdl import block, always_comb

from flow import FlowControl
from utils import clone_signal
from vector_utils import reduce_and


class Pipeline:
    def __init__(self, flow: FlowControl):
        self._flow = flow
        self._stages = []

    @block
    def create(self):
        insts = []
        pre_fin = self._flow.enb
        for stage_components in self._stages:
            stage_fin_signals = []
            for component in stage_components:
                subflow = self._flow.create_subflow(enb=pre_fin)
                stage_fin_signals.append(subflow.fin)
                insts.append(block(component)(subflow))
            if len(stage_fin_signals) == 1:
                pre_fin = stage_fin_signals[0]
            elif len(stage_fin_signals) > 1:
                stage_fin = clone_signal(pre_fin)
                insts.append(reduce_and(stage_fin_signals, stage_fin))
                pre_fin = stage_fin

        @always_comb
        def assign():
            self._flow.fin.next = pre_fin

        return insts + [assign]

    def append(self, mod, *args):
        self._stages.append([lambda flow: mod(*args, flow=flow)])
        return self

    def append_lda(self, lda):
        self._stages.append([lda])
        return self
