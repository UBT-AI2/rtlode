from dataclasses import dataclass
from typing import List

from myhdl import block, instances, ResetSignal, SignalType, always

import num
from config import Config
from rk_stage import stage
from utils import FlowControl, Pipeline, clone_signal, clone_signal_structure
from vector_utils import lincomb_flow, reduce_and


@dataclass
class RKInterface:
    flow: FlowControl
    h: SignalType
    n: SignalType
    x_start: SignalType
    y_start: List[SignalType]
    x: SignalType
    y: List[SignalType]


@block
def runge_kutta(config: Config, interface: RKInterface):
    insts = []

    x_n = clone_signal(interface.x)
    y_n = clone_signal_structure(interface.y)

    v = [clone_signal_structure(y_n) for _ in range(config.stages)]

    stage_reset = ResetSignal(False, True, False)
    stage_flow = interface.flow.create_subflow(rst=stage_reset, enb=interface.flow.enb)
    stage_pipe = Pipeline(stage_flow)
    for si in range(config.stages):
        # TODO use parallel stage calc if possible
        stage_pipe.append_lda(
            lambda flow, cfg=config.get_stage_config(si):
            stage(cfg, flow, interface.h, interface.x, interface.y, v)
        )
    insts.append(stage_pipe.create())

    insts.append(num.add(interface.x, interface.h, x_n))

    y_subflows = [interface.flow.create_subflow(rst=stage_reset, enb=stage_flow.fin) for _ in range(config.system_size)]
    @block
    def calc_y_n(i):
        y_lincomb_inst_res = clone_signal(y_n[i])
        y_mul_inst_res = clone_signal(y_n[i])

        return Pipeline(y_subflows[i])\
            .append(
                lincomb_flow,
                [clone_signal(y_n[i], value=num.from_float(el)) for el in config.b],
                [el[i] for el in v],
                y_lincomb_inst_res
            )\
            .append(num.mul_flow, interface.h, y_lincomb_inst_res, y_mul_inst_res)\
            .append(num.add_flow, interface.y[i], y_mul_inst_res, y_n[i])\
            .create()
    insts.append([calc_y_n(i) for i in range(config.system_size)])

    step_fin = clone_signal(interface.flow.fin)
    insts.append([reduce_and([sf.fin for sf in y_subflows], step_fin)])

    step_counter = clone_signal(interface.n)
    @always(interface.flow.clk_edge(), interface.flow.rst.posedge)
    def calc_final():
        if interface.flow.rst == interface.flow.rst.active:
            interface.x.next = interface.x_start
            for i in range(config.system_size):
                interface.y[i].next = interface.y_start[i]
            stage_reset.next = True
        else:
            if interface.flow.fin:
                pass
            elif stage_reset:
                stage_reset.next = False
            elif step_fin:
                # Copy calculated values to working ones
                interface.x.next = x_n
                for i in range(config.system_size):
                    interface.y[i].next = y_n[i]
                # Increase step counter
                step_counter.next = step_counter + 1
                # Reset all stages
                stage_reset.next = True

                # Print debug informations
                for i in range(config.system_size):
                    if __debug__:
                        print('%d %f: %s : %f' % (
                            i,
                            num.to_float(x_n),
                            list(map(num.to_float, [el[i] for el in v])),
                            num.to_float(y_n[i])
                        ))

                if step_counter + 1 >= interface.n:
                    interface.flow.fin.next = True

    return instances()
