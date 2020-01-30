from typing import List

from myhdl import block, always_comb

from flow import FlowControl
from utils import clone_signal
from vector_utils import reduce_and


def bind(mod, *args):
    def _bind(flow, _args=args):
        return mod(*args, flow)
    return _bind


class Pipeline:
    def __init__(self):
        self._stages = []

    @block
    def create(self, flow: FlowControl):
        insts = []
        pre_fin = flow.enb
        for stage_components in self._stages:
            stage_fin_signals = []
            for component in stage_components:
                subflow = flow.create_subflow(enb=pre_fin)
                stage_fin_signals.append(subflow.fin)
                if isinstance(component, Pipeline):
                    insts.append(component.create(subflow))
                elif callable(component):
                    insts.append(block(component)(subflow))
                else:
                    raise Exception('Unknown internal error')
            if len(stage_fin_signals) == 1:
                pre_fin = stage_fin_signals[0]
            elif len(stage_fin_signals) > 1:
                stage_fin = clone_signal(pre_fin)
                insts.append(reduce_and(stage_fin_signals, stage_fin))
                pre_fin = stage_fin

        @always_comb
        def assign():
            flow.fin.next = pre_fin

        return insts + [assign]

    def append(self, components):
        if isinstance(components, List):
            self._stages.append(components)
        else:
            self._stages.append([components])
        return self
