from typing import List, Union, Callable
from myhdl import block, always_comb

from generator.flow import FlowControl
from generator.utils import clone_signal
from generator.vector_utils.reduce import reduce_and


class Pipeline:
    """
    Allows simple creation of sequential and parallel logic.
    Order of execution is managed by flow interface.
    """
    def __init__(self):
        self._stages = []

    @block
    def create(self, flow: FlowControl):
        """
        Build up pipeline and return all myhdl instances.

        :param flow: flow interface to control the whole pipe
        :return: myhdl instances
        """
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

    component = Union['Pipeline', Callable]

    def then(self, components: Union[List[component], component]) -> 'Pipeline':
        """
        Defines next logic step of pipeline.
        These can either be a list of components which should be processed in parallel
        or a single component.

        :param components: components to be executed in next logic step
        :return: pipe object
        """
        if isinstance(components, List):
            self._stages.append(components)
        else:
            self._stages.append([components])
        return self
