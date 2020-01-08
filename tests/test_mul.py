import unittest

from myhdl import Simulation, Signal, delay, traceSignals, intbv

import num


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
        clk = Signal(bool(0))

        def test():
            yield delay(10)
            clk.next = not clk  # High
            yield delay(10)
            clk.next = not clk
            yield delay(10)
            clk.next = not clk  # High
            yield delay(10)
            self.assertEqual(num.from_float(a * b), out_c)

        self.runTest(in_a, in_b, out_c, test, clk=clk)

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
    def runTest(in_a, in_b, out_sum, test, clk=None):
        dut = num.mul(in_a, in_b, out_sum, clk=clk)
        check = test()
        sim = Simulation(dut, check)
        sim.run(quiet=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
