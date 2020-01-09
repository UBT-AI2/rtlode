import unittest

from myhdl import Simulation, Signal, delay

import num
from expr_parser import expr


class TestExpr(unittest.TestCase):
    def test_expr(self):

        clk = Signal(bool(0))
        scope = {
            'x': [Signal(num.from_float(5))]
        }
        out = Signal(num.default())

        def test():
            for i in range(2 * 5):
                yield delay(10)
                clk.next = not clk

            self.assertEqual(num.from_float(17), out)

        self.runTest('3*4+x[0]', scope, out, test, clk=clk)

    @staticmethod
    def runTest(expression, scope, out, test, clk=None):
        dut = expr(expression, scope, out, clk=clk)
        check = test()
        sim = Simulation(dut, check)
        sim.run(quiet=1)
