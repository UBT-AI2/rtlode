from dataclasses import dataclass, field, InitVar
from typing import List

from myhdl import block, instances, ResetSignal, SignalType, always, Signal

import generator.calc
from utils import num
from common.config import Config
from generator.rk_calc import pipe_calc_step
from generator.rk_stage import stage
from generator.utils import clone_signal, clone_signal_structure, bind
from generator.flow import FlowControl
from generator.pipeline import Pipeline


@dataclass
class SolverInterface:
    """
    Internal runge kutta interface used by the solver.
    """
    system_size: InitVar[int]
    flow: FlowControl = field(default_factory=FlowControl)
    h: SignalType = field(default_factory=lambda: Signal(num.default()))
    n: SignalType = field(default_factory=lambda: Signal(num.integer()))
    x_start: SignalType = field(default_factory=lambda: Signal(num.default()))
    y_start: List[SignalType] = field(default=None)
    x: SignalType = field(default_factory=lambda: Signal(num.default()))
    y: List[SignalType] = field(default=None)

    def __post_init__(self, system_size):
        if self.y_start is None:
            self.y_start = [Signal(num.default()) for _ in range(system_size)]
        if self.y is None:
            self.y = [Signal(num.default()) for _ in range(system_size)]


@block
def rk_solver(config: Config, interface: SolverInterface):
    """
    Implements logic for a rk solver.

    :param config: configuration parameters for the solver
    :param interface: internal interface
    :return:
    """
    x_n = clone_signal(interface.x)
    y_n = clone_signal_structure(interface.y)

    v = [clone_signal_structure(y_n) for _ in range(config.stages)]

    pipe_reset = ResetSignal(False, True, False)
    pipe_enb = Signal(bool(0))
    pipe_flow = interface.flow.create_subflow(rst=pipe_reset, enb=pipe_enb)
    pipe = Pipeline()

    stage_pipe = Pipeline()
    for si in range(config.stages):
        # TODO use parallel stage calc if possible
        stage_pipe.then(
            bind(stage, config.get_stage_config(si), interface.h, interface.x, interface.y, v)
        )
    pipe.then([stage_pipe, bind(generator.calc.add, interface.x, interface.h, x_n)])

    pipe.then([pipe_calc_step(
        [clone_signal(y_n[i], value=num.from_float(el)) for el in config.b],
        [el[i] for el in v],
        interface.h,
        interface.y[i],
        y_n[i]
    ) for i in range(config.system_size)])
    pipe_insts = pipe.create(pipe_flow)

    step_counter = clone_signal(interface.n)
    @always(interface.flow.clk_edge())
    def calc_final():
        if interface.flow.rst == interface.flow.rst.active:
            pipe_reset.next = True
            pipe_enb.next = False
            interface.flow.fin.next = False
            step_counter.next = 0
        else:
            if not interface.flow.enb or interface.flow.fin:
                pass
            else:
                if not pipe_enb:
                    interface.x.next = interface.x_start
                    for i in range(config.system_size):
                        interface.y[i].next = interface.y_start[i]
                    pipe_enb.next = True
                elif pipe_reset:
                    pipe_reset.next = False
                elif pipe_flow.fin:
                    # Copy calculated values to working ones
                    interface.x.next = x_n
                    for i in range(config.system_size):
                        interface.y[i].next = y_n[i]
                    # Increase step counter
                    step_counter.next = step_counter + 1
                    # Reset all stages
                    pipe_reset.next = True

                    # Print debug informations
                    if __debug__:
                        for i in range(config.system_size):
                            print('%d %f: %s : %f' % (
                                i,
                                num.to_float(x_n),
                                list(map(num.to_float, [el[i] for el in v])),
                                num.to_float(y_n[i])
                            ))

                    if step_counter + 1 >= interface.n:
                        interface.flow.fin.next = True

    return instances()
