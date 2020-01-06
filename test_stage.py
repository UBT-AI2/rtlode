from random import randrange
import unittest

from myhdl import Signal, Simulation, ResetSignal, delay

import num
from runge_kutta import stage

# TODO: Reset testen


class TestStage(unittest.TestCase):
    testdata = [
        # c_a, c_c, in_x, in_h, in_v, in_y
        [[0.5], 0.5, 0, 0.1, [3], 2],
        [[0.5], 0,   0, 0.1, [3], 2],
        [[0.5], 0.5, 0,   1, [3], 2],
        [[0.75], 0.5, 0, 0.1, [1], 3],
        [[], 0.5, 0, 0.1, [], 3],
    ]

    def test_stage(self):
        """Check sample data."""

        for td in self.testdata:
            c_a = list(map(num.from_float, td[0]))
            c_c = num.from_float(td[1])

            def test(clk, rst, enable, in_x, in_h, in_v, in_y, out_finished, out_v):
                in_x.next = num.from_float(td[2])
                in_h.next = num.from_float(td[3])
                for i in range(len(td[4])):
                    in_v[i].next = num.from_float(td[4][i])
                in_y.next = num.from_float(td[5])
                enable.next = 1

                for i in range(2 * 5):
                    yield delay(10)
                    clk.next = not clk

                res_lincomb = 0
                for i in range(len(td[0])):
                    res_lincomb += td[0][i] * td[4][i]

                self.assertEqual(True, out_finished)
                self.assertAlmostEqual(num.from_float(2 * (td[5] + td[3] * res_lincomb)), out_v, delta=5, msg=td)

            self.runTest(c_a, c_c, test)

    @staticmethod
    def runTest(c_a, c_c, test):
        clk = Signal(bool(0))
        rst = ResetSignal(False, True, False)
        enable = Signal(bool(0))

        in_x = Signal(num.default())
        in_h = Signal(num.default())
        in_v = [Signal(num.default()) for _ in range(len(c_a))]
        in_y = Signal(num.default())
        out_finished = Signal(bool(0))
        out_v = Signal(num.default())

        dut = stage(c_a, c_c, clk, rst, enable, in_x, in_h, in_v, in_y, out_finished, out_v)
        check = test(clk, rst, enable, in_x, in_h, in_v, in_y, out_finished, out_v)
        sim = Simulation(dut, check)
        sim.run(quiet=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
