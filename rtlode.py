import os
import sys

import yaml
from myhdl import Simulation, Signal, ResetSignal, delay, block

import num
from config import Config
from interface import SeqInterface, wrapper_seq
from runge_kutta import rk_solver, RKInterface
from flow import FlowControl


def print_help():
    print("%s sim <method.yaml> <ivp.yaml>" % (sys.argv[0]))


def load_yaml(file):
    with open(file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc


def sim(method_file, ivp_file):
    method = load_yaml(method_file)
    ivp = load_yaml(ivp_file)
    cfg = Config(method['A'], method['b'], method['c'], ivp['components'])

    clk = Signal(bool(0))
    rst = ResetSignal(False, True, False)
    enable = Signal(bool(0))
    finished = Signal(bool(0))

    h = Signal(num.from_float(ivp['h']))
    n = Signal(num.integer(ivp['n']))
    x_start = Signal(num.from_float(ivp['x']))
    y_start = [Signal(num.from_float(ivp['y'][i])) for i in range(cfg.system_size)]
    x = Signal(num.default())
    y = [Signal(num.default()) for _ in range(cfg.system_size)]

    interface = RKInterface(FlowControl(clk, rst, enable, finished), h, n, x_start, y_start, x, y)

    def test():
        rst.next = True
        yield delay(10)
        clk.next = not clk
        yield delay(10)
        clk.next = not clk
        rst.next = False
        yield delay(10)
        clk.next = not clk
        yield delay(10)
        clk.next = not clk
        yield delay(10)
        clk.next = not clk
        yield delay(10)
        clk.next = not clk
        enable.next = 1

        clks = 0
        while finished != 1:
            yield delay(10)
            clk.next = not clk
            clks += 1
            yield delay(10)
            clk.next = not clk

        print("Finished after %i clock cycles." % clks)

    dut = rk_solver(cfg, interface)
    testdriver = test()
    sim_inst = Simulation(dut, testdriver)
    sim_inst.run(quiet=1)


def convert(method_file, ivp_file):
    method = load_yaml(method_file)
    ivp = load_yaml(ivp_file)
    cfg = Config(method['A'], method['b'], method['c'], ivp['components'])

    clk = Signal(bool(0))
    rst = ResetSignal(False, True, False)
    enable = Signal(bool(0))
    finished = Signal(bool(0))

    h = Signal(num.default())
    n = Signal(num.integer())
    x_start = Signal(num.default())
    y_start_addr = Signal(num.integer())
    y_start_val = Signal(num.default())
    x = Signal(num.default())
    y_addr = Signal(num.integer())
    y_val = Signal(num.default())

    interface = SeqInterface(
        FlowControl(clk, rst, enable, finished),
        h,
        n,
        x_start,
        y_start_addr,
        y_start_val,
        x,
        y_addr,
        y_val
    )

    wrapper_inst = wrapper_seq(cfg, interface)
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'runtime', 'hw', 'generated')
    wrapper_inst.convert(hdl='Verilog', testbench=False, name='solver', path=dir_path)


def rtlode():
    if len(sys.argv) < 4:
        print_help()
    elif sys.argv[1] == 'sim':
        sim(sys.argv[2], sys.argv[3])
    else:
        print("Unknown or not yet implemented subfunction.")
        print_help()


if __name__ == '__main__':
    rtlode()
