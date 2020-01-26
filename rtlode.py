import sys

import yaml
from myhdl import Simulation, Signal, ResetSignal, delay

import num
from config import Config
from runge_kutta import runge_kutta, Interface
from utils import FlowControl


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

    interface = Interface(FlowControl(clk, rst, enable, finished), h, n, x_start, y_start, x, y)

    def test():
        rst.next = True
        yield delay(10)
        clk.next = not clk
        yield delay(10)
        clk.next = not clk
        rst.next = False
        enable.next = 1

        clks = 0
        while finished != 1:
            yield delay(10)
            clk.next = not clk
            clks += 1
            yield delay(10)
            clk.next = not clk

        print("Finished after %i clock cycles." % clks)

    dut = runge_kutta(cfg, interface)
    testdriver = test()
    sim_inst = Simulation(dut, testdriver)
    sim_inst.run(quiet=1)


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
