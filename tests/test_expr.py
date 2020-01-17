import unittest

from myhdl import Simulation, Signal, delay

import num
from expr_parser import expr


class TestExpr(unittest.TestCase):
    testset = [
        ('mixed base test', '3*4+y[0]*x', {
            'x': 2,
            'y': [5]
        }, 22),
        ('multiple sign ops', '--+-3', {}, -3),
        ('no op', '3', {}, 3),
        ('no op decimal', '3.15', {}, 3.15),
        ('no op var', 'x', {'x': 3}, 3),
        ('var indexing', 'x[0]', {'x': [3]}, 3),
        ('parenthese', '(3)', {}, 3),
        ('multiple parenthese', '(((3)))', {}, 3),
        ('sign op with var', '-x', {'x': 3}, -3),
        ('add op with var', '2+x', {'x': 3}, 5),
        ('sub op with var', '2-x', {'x': 3}, -1),
        ('mul op with var', '2*x', {'x': 3}, 6),
        ('mul ops of same hierarchy', '3*3*3', {}, 27),
        ('add and sub ops of same hierarchy', '3+2-1', {}, 4),
        ('mul add priorization', '3+2*4', {}, 11),
        ('parenthese priorization', '(3+2)*4', {}, 20),
    ]

    def test_expr(self):
        """Checking whole testset with different aspects."""

        for test in self.testset:
            clk = Signal(bool(0))
            out = Signal(num.default())

            (desc, expr_str, scope, res) = test

            def convert_scope(data):
                if isinstance(data, int) or isinstance(data, float):
                    return Signal(num.from_float(data))
                elif isinstance(data, list):
                    return list(map(convert_scope, data))
                elif isinstance(data, dict):
                    res_data = {}
                    for var in data:
                        res_data[var] = convert_scope(data[var])
                    return res_data
                raise Exception('Can\'t convert data chunk to signals.')

            scope = convert_scope(scope)
            res = num.from_float(res)

            def test():
                for i in range(2 * 5):
                    yield delay(10)
                    clk.next = not clk

                self.assertEqual(res, out, msg='%s: %s' % (desc, expr_str))

            self.runTest(expr_str, scope, out, test, clk=clk)

    @staticmethod
    def runTest(expression, scope, out, test, clk=None):
        dut = expr(expression, scope, out, clk=clk)
        check = test()
        sim = Simulation(dut, check)
        sim.run(quiet=1)
