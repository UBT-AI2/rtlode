from dataclasses import dataclass

from myhdl import block, SignalType, always_seq, instances

from generator.config import Config
from generator.runge_kutta import rk_solver, RKInterface
from generator.utils import clone_signal
from generator.flow import FlowControl


@dataclass
class SeqInterface:
    """
    Defines the sequential interface used to control solver externally.
    """
    flow: FlowControl
    h: SignalType
    n: SignalType
    x_start: SignalType
    y_start_addr: SignalType
    y_start_val: SignalType
    x: SignalType
    y_addr: SignalType
    y_val: SignalType


@block
def wrapper_seq(config: Config, interface: SeqInterface):
    """
    Wrapper logic to port internally solver interface to external sequential interface.
    Internal interface uses list of signals to enable pleasant implementation.

    :param config: configuration parameters for the solver
    :param interface: external sequential interface
    :return: myhdl instances of solvers
    """
    y_start = [clone_signal(interface.y_start_val) for _ in range(config.system_size)]
    y = [clone_signal(interface.y_start_val) for _ in range(config.system_size)]

    rk_interface = RKInterface(
        interface.flow,
        interface.h,
        interface.n,
        interface.x_start,
        y_start,
        interface.x,
        y
    )

    @always_seq(interface.flow.clk_edge(), reset=None)
    def handle_set():
        for index in range(config.system_size):
            if interface.y_start_addr == index:
                y_start[index].next = interface.y_start_val
            if interface.y_addr == index:
                interface.y_val.next = y[index]

    rk_insts = rk_solver(config, rk_interface)

    return instances()
