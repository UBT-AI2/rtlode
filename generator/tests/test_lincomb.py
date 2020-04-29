from random import randrange
import unittest

from myhdl import Signal, intbv, delay, Simulation, ResetSignal

from generator.flow import FlowControl
from utils import num
from generator.vector_utils.lincomb import UnequalVectorLength, lincomb


class TestLincomb(unittest.TestCase):
    def test_lincomb_unequal_vector_len(self):
        """Check if vector of length 0 is working."""

        in_a = [Signal(num.from_float(0)), Signal(num.from_float(1))]
        in_b = [Signal(num.from_float(0.5))]
        out_sum = Signal(num.default())
        flow = FlowControl(
            Signal(bool(0)),
            ResetSignal(True, False, True),
            Signal(bool(1)),
            Signal(bool(0))
        )

        def test():
            while not flow.fin:
                yield delay(10)
                flow.clk.next = not flow.clk
                yield delay(10)
                flow.clk.next = not flow.clk
            self.assertEqual(0, out_sum)

        self.assertRaises(UnequalVectorLength, self.runTest, in_a, in_b, out_sum, flow, test)

    def test_lincomb_no_element(self):
        """Check if vector of length 0 is working."""

        in_a = []
        in_b = []
        out_sum = Signal(num.default())
        flow = FlowControl(
            Signal(bool(0)),
            ResetSignal(True, False, True),
            Signal(bool(1)),
            Signal(bool(0))
        )

        def test():
            while not flow.fin:
                yield delay(10)
                flow.clk.next = not flow.clk
                yield delay(10)
                flow.clk.next = not flow.clk
            self.assertEqual(0, out_sum)

        self.runTest(in_a, in_b, out_sum, flow, test)

    def test_lincomb_one_element(self):
        """Check if vector of length 1 is working."""

        a = randrange(-10, 10)
        b = randrange(-10, 10)

        in_a = [Signal(num.from_float(a))]
        in_b = [Signal(num.from_float(b))]
        out_sum = Signal(num.default())
        flow = FlowControl(
            Signal(bool(0)),
            ResetSignal(True, False, True),
            Signal(bool(1)),
            Signal(bool(0))
        )

        def test():
            while not flow.fin:
                yield delay(10)
                flow.clk.next = not flow.clk
                yield delay(10)
                flow.clk.next = not flow.clk
            self.assertEqual(num.from_float(a * b), out_sum)

        self.runTest(in_a, in_b, out_sum, flow, test)

    def test_lincomb(self):
        """Check if longer vectors are working."""

        n = 10
        a = [randrange(-10, 10) for i in range(n)]
        b = [randrange(-10, 10) for i in range(n)]

        in_a = [Signal(num.from_float(a[i])) for i in range(n)]
        in_b = [Signal(num.from_float(b[i])) for i in range(n)]
        out_sum = Signal(intbv(0))
        flow = FlowControl(
            Signal(bool(0)),
            ResetSignal(True, False, True),
            Signal(bool(1)),
            Signal(bool(0))
        )

        result = 0
        for i in range(n):
            result += a[i] * b[i]

        def test():
            while not flow.fin:
                yield delay(10)
                flow.clk.next = not flow.clk
                yield delay(10)
                flow.clk.next = not flow.clk
            self.assertEqual(num.from_float(result), out_sum)

        self.runTest(in_a, in_b, out_sum, flow, test)

    @staticmethod
    def runTest(in_a, in_b, out_sum, flow, test):
        dut = lincomb(in_a, in_b, out_sum, flow)
        check = test()
        sim = Simulation(dut, check)
        sim.run(quiet=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
