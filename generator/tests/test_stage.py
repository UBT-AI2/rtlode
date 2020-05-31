import unittest

from myhdl import Signal, Simulation, ResetSignal, delay

from utils import num
from generator.rk_stage import stage
from generator.config import StageConfig

# TODO: Reset testen
from generator.flow import FlowControl


class TestStage(unittest.TestCase):
    testdata = [
        # c_a, c_c, in_x, in_h, in_v, in_y
        [[], 0.5, 0, 0.1, [], 3],
        [[0.5], 0.5, 0, 0.1, [3], 2],
        [[0.5], 0,   0, 0.1, [3], 2],
        [[0.5], 0.5, 0,   1, [3], 2],
        [[0.75], 0.5, 0, 0.1, [1], 3],
    ]

    def test_stage(self):
        """Check sample data."""

        for td in self.testdata:
            c_a = td[0]
            c_c = td[1]

            print(td)

            def test(flow, in_h, in_x, in_y, in_v):
                in_x.next = num.signal_from_float(td[2])
                in_h.next = num.signal_from_float(td[3])
                for i in range(len(td[4])):
                    in_v[i][0].next = num.signal_from_float(td[4][i])
                in_y[0].next = num.signal_from_float(td[5])
                flow.enb.next = 1

                clks = 0
                while not flow.fin:
                    yield delay(10)
                    flow.clk.next = not flow.clk
                    clks += 1
                    yield delay(10)
                    flow.clk.next = not flow.clk

                print("Finished after %i clock cycles." % clks)

                res_lincomb = 0
                for i in range(len(td[0])):
                    res_lincomb += td[0][i] * td[4][i]

                self.assertAlmostEqual(num.signal_from_float(2 * (td[5] + td[3] * res_lincomb)), in_v[len(c_a)][0], delta=20000, msg=td)

            self.runTest(c_a, c_c, test)

    @staticmethod
    def runTest(c_a, c_c, test):
        clk = Signal(bool(0))
        rst = ResetSignal(False, True, False)
        enable = Signal(bool(0))
        finished = Signal(bool(0))

        in_x = Signal(num.default())
        in_h = Signal(num.default())
        in_v = [[Signal(num.default())] for _ in range(len(c_a) + 1)]
        in_y = [Signal(num.default())]

        config = StageConfig(len(c_a), c_a, c_c, ['2*y[0]'])
        flow = FlowControl(clk, rst, enable, finished)

        dut = stage(config, flow, in_h, in_x, in_y, in_v)
        check = test(flow, in_h, in_x, in_y, in_v)
        sim = Simulation(dut, check)
        sim.run(quiet=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
