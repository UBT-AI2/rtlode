import sys

import yaml
from myhdl import Simulation, Signal, ResetSignal, delay

from runge_kutta import runge_kutta


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

    clk = Signal(bool(0))
    rst = ResetSignal(False, True, False)
    enable = Signal(bool(0))
    finished = Signal(bool(0))

    def test():
        enable.next = 1

        clks = 0
        while finished != 1:
            yield delay(10)
            clk.next = not clk
            clks += 1
            yield delay(10)
            clk.next = not clk

        print("Finished after %i clock cycles." % clks)

    dut = runge_kutta(clk, rst, enable, finished, method, ivp)
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
