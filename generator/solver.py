from dataclasses import dataclass, field, InitVar
from typing import List

from myhdl import block, instances, ResetSignal, SignalType, always, Signal, enum, always_comb

import generator.calc
from common import data_desc
from generator.cdc_utils import AsyncFifoConsumer, AsyncFifoProducer
from utils import num
from generator.config import Config
from generator.rk_calc import pipe_calc_step
from generator.rk_stage import stage
from generator.utils import clone_signal, clone_signal_structure, bind, assign, assign_2
from generator.flow import FlowControl
from generator.pipeline import Pipeline

t_state = enum('READY', 'BUSY', 'FINISHED')


@dataclass
class SolverData:
    """
    Internal runge kutta interface used by the solver.
    """
    system_size: InitVar[int]
    id: SignalType = field(default_factory=lambda: Signal(num.integer()))
    h: SignalType = field(default_factory=lambda: Signal(num.default()))
    n: SignalType = field(default_factory=lambda: Signal(num.integer()))
    x: SignalType = field(default_factory=lambda: Signal(num.default()))
    y: List[SignalType] = field(default=None)

    def __post_init__(self, system_size):
        if self.y is None:
            self.y = [Signal(num.default()) for _ in range(system_size)]


@block
def solver(
        config: Config,
        clk: SignalType,
        rst: SignalType,
        data_in: AsyncFifoConsumer,
        data_out: AsyncFifoProducer,
        rdy: SignalType,
        rdy_ack: SignalType,
        fin: SignalType,
        fin_ack: SignalType,
):
    state = Signal(t_state.READY)

    solver_input_desc = data_desc.get_input_desc(config.system_size)
    solver_input = solver_input_desc.create_read_instance(data_in.data)

    solver_output_desc = data_desc.get_output_desc(config.system_size)
    solver_output = solver_output_desc.create_write_instance()
    solver_output_packed = solver_output.packed()

    data = SolverData(config.system_size)

    x_n = clone_signal(data.x)
    y_n = clone_signal_structure(data.y)

    v = [clone_signal_structure(y_n) for _ in range(config.stages)]

    pipe_flow = FlowControl(clk=clk, rst=ResetSignal(False, True, False), enb=Signal(bool(0)))
    pipe = Pipeline()

    stage_pipe = Pipeline()
    for si in range(config.stages):
        # TODO use parallel stage calc if possible
        stage_pipe.then(
            stage(config.get_stage_config(si), data.h, data.x, data.y, v)
        )
    pipe.then([stage_pipe, bind(generator.calc.add, data.x, data.h, x_n)])

    pipe.then([pipe_calc_step(
        [num.int_from_float(el) for el in config.b],
        [el[i] for el in v],
        data.h,
        data.y[i],
        y_n[i]
    ) for i in range(config.system_size)])
    pipe_insts = pipe.create(pipe_flow)

    step_counter = clone_signal(data.n)

    @always(clk.posedge)
    def state_machine():
        if rst:
            state.next = t_state.READY
            rdy.next = True
            fin.next = False
        else:
            if state == t_state.READY:
                # If Prio ACK, set solver input and change to BUSY
                data.id.next = solver_input.id
                data.h.next = solver_input.h
                data.n.next = solver_input.n
                data.x.next = solver_input.x_start
                # Assign y_start
                step_counter.next = 0

                if data_in.rd and not data_in.empty and rdy_ack:
                    state.next = t_state.BUSY
                    rdy.next = False
                    pipe_flow.enb.next = True
                    pipe_flow.rst.next = False
            elif state == t_state.BUSY:
                if pipe_flow.rst:
                    pipe_flow.rst.next = False
                elif pipe_flow.fin:
                    # One step finished

                    # Copy calculated values to working ones
                    data.x.next = x_n
                    # Increase step counter
                    step_counter.next = step_counter + 1
                    # Reset all stages
                    pipe_flow.rst.next = True

                    # Print debug informations
                    if __debug__:
                        for i in range(config.system_size):
                            print('%d %f: %s : %f' % (
                                i,
                                num.to_float(x_n),
                                list(map(num.to_float, [el[i] for el in v])),
                                num.to_float(y_n[i])
                            ))

                    if step_counter + 1 >= data.n:
                        state.next = t_state.FINISHED
                        fin.next = True
            elif state == t_state.FINISHED:
                # If Prio ACK, set solver output and change to READY
                solver_output.id.next = data.id
                solver_output.x.next = data.x
                # Assign y

                if data_out.wr and not data_out.full and fin_ack:
                    state.next = t_state.READY
                    pipe_flow.rst.next = True
                    pipe_flow.enb.next = False
                    fin.next = False
                    rdy.next = True

    state_ready = Signal(bool(0))
    state_step_finished = Signal(bool(0))
    state_finished = Signal(bool(0))

    @always_comb
    def set_state_ready():
        state_ready.next = state == t_state.READY

    @always_comb
    def set_state_step_finished():
        state_step_finished.next = state == t_state.BUSY and pipe_flow.fin

    @always_comb
    def set_state_finished():
        state_finished.next = state == t_state.FINISHED

    assign_y = [
        assign_2(clk, state_ready, solver_input.y_start[i], state_step_finished, y_n[i], data.y[i])
        for i in range(config.system_size)
    ]

    assign_y_out = [
        assign(clk, state_finished, data.y[i], solver_output.y[i])
        for i in range(config.system_size)
    ]

    @always_comb
    def assign_solver_output():
        data_out.data.next = solver_output_packed

    return instances()
