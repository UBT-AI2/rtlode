import unittest

from myhdl import Simulation, Signal, delay, ResetSignal

import generator.calc
from generator.flow import FlowControl
from utils import num


class TestMul(unittest.TestCase):
    def test_mul_comb(self):
        """Check if combinatorical logic is working."""

        in_a = Signal(num.from_float(2.5))
        in_b = Signal(num.from_float(10))
        out_sum = Signal(num.default())

        def test():
            yield delay(1)
            self.assertEqual(25, num.to_float(out_sum))

        self.runTest(in_a, in_b, out_sum, test)

    def test_mul_seq(self):
        """Check if sequential logic is working."""

        a = 2.5
        b = 10

        in_a = Signal(num.from_float(a))
        in_b = Signal(num.from_float(b))
        out_c = Signal(num.default())
        flow = FlowControl(
            Signal(bool(0)),
            ResetSignal(True, False, True),
            Signal(bool(1)),
            Signal(bool(0))
        )

        def test():
            clks = 0
            while not flow.fin:
                yield delay(10)
                flow.clk.next = not flow.clk
                clks += 1
                yield delay(10)
                flow.clk.next = not flow.clk

            print("Finished after %i clock cycles." % clks)

            self.assertEqual(num.from_float(a * b), out_c)

        self.runTest(in_a, in_b, out_c, test, flow=flow)

    def test_mul_negative_result(self):
        """Check signed multiplication."""

        in_a = Signal(num.from_float(-2.5))
        in_b = Signal(num.from_float(10))
        out_sum = Signal(num.default())

        def test():
            yield delay(1)
            self.assertEqual(-25, num.to_float(out_sum))

        self.runTest(in_a, in_b, out_sum, test)

    def test_mul_zero(self):
        """Check multiplication with zero."""

        in_a = Signal(num.from_float(0))
        in_b = Signal(num.from_float(10))
        out_sum = Signal(num.default())

        def test():
            yield delay(1)
            self.assertEqual(0, num.to_float(out_sum))

        self.runTest(in_a, in_b, out_sum, test)

    @staticmethod
    def runTest(in_a, in_b, out_sum, test, flow=None):
        dut = generator.calc.mul(in_a, in_b, out_sum, flow=flow)
        check = test()
        sim = Simulation(dut, check)
        sim.run(quiet=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
