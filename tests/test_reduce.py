import unittest
from random import randrange

from myhdl import Signal, intbv, Simulation, delay

from utils import reduce_sum


class TestReduce(unittest.TestCase):
    def test_reduce_no_element(self):
        """Check if vector of length 0 is working."""

        vector = []
        out_sum = Signal(intbv(0))

        def test():
            yield delay(10)
            self.assertEqual(0, out_sum)
            pass

        self.runTest(vector, out_sum, test)

    def test_reduce_one_element(self):
        """Check if vector of length 1 is working."""

        vector = [Signal(intbv(0)) for i in range(1)]
        out_sum = Signal(intbv(0))

        def test():
            vector[0].next = 50
            yield delay(10)
            self.assertEqual(vector[0], out_sum)
            pass

        self.runTest(vector, out_sum, test)

    def test_reduce(self):
        """Check base sum capabilities."""

        n = 100
        values = [randrange(-10, 10) for i in range(n)]

        in_vector = [Signal(intbv(values[i])) for i in range(n)]
        out_sum = Signal(intbv(0))

        def test():
            yield delay(10)
            self.assertEqual(sum(values), out_sum)
            pass

        self.runTest(in_vector, out_sum, test)

    @staticmethod
    def runTest(vector, sum, test):
        dut = reduce_sum(vector, sum)
        check = test()
        sim = Simulation(dut, check)
        sim.run(quiet=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
