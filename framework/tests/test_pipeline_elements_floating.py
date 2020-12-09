from framework.pipeline import PipeConstant
from framework.pipeline_elements import add, mul, negate
from framework.tests.helper import PipeTestCase
from utils import num


class TestPipe(PipeTestCase):
    def run(self, result=None):
        # Run twice for each floating precission
        num.set_numeric_factory(num.FloatingNumberFactory(num.FloatingPrecission.DOUBLE))
        super().run(result)
        num.set_numeric_factory(num.FloatingNumberFactory(num.FloatingPrecission.SINGLE))
        super().run(result)

    def test_add(self):
        """
        Testing addition.
        """
        def inner_pipe(data):
            res = data + PipeConstant.from_float(5)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i + 5 for i in range(40)])

    def test_add_reverse(self):
        """
        Testing addition reverse operator.
        """
        def inner_pipe(data):
            res = PipeConstant.from_float(5) + data
            return res

        self.run_pipe(inner_pipe, list(range(40)), [5 + i for i in range(40)])

    def test_add_only_constants(self):
        """
        Testing multiplication with two constants.
        """
        def inner_pipe(data):
            add1 = add(PipeConstant.from_float(2), PipeConstant.from_float(3))
            add2 = add(data, add1)
            return add2

        self.run_pipe(inner_pipe, list(range(40)), [i + 5 for i in range(40)])

    def test_sub(self):
        """
        Testing substraction.
        """
        def inner_pipe(data):
            res = data - PipeConstant.from_float(5)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i - 5 for i in range(40)])

    def test_sub_reverse(self):
        """
        Testing substraction reverse operator.
        """
        def inner_pipe(data):
            res = PipeConstant.from_float(5) - data
            return res

        self.run_pipe(inner_pipe, list(range(40)), [5 - i for i in range(40)])

    def test_negate(self):
        """
        Testing substraction.
        """
        def inner_pipe(data):
            res = negate(data)
            return res

        self.run_pipe(inner_pipe, list(range(1, 40)), [-i for i in range(1, 40)])

    def test_mul_only_constants(self):
        """
        Testing multiplication with two constants.
        """
        def inner_pipe(data):
            mul1 = mul(PipeConstant.from_float(2), PipeConstant.from_float(3))
            add1 = add(data, mul1)
            return add1

        self.run_pipe(inner_pipe, list(range(40)), [i + 6 for i in range(40)])

    def test_mul_by_constant(self):
        """
        Testing multiplication with constant factor.
        """
        def inner_pipe(data):
            mul1 = mul(data, PipeConstant.from_float(3))
            add1 = add(mul1, PipeConstant.from_float(3))
            return add1

        self.run_pipe(inner_pipe, list(range(40)), [(i * 3) + 3 for i in range(40)])

    def test_mul(self):
        """
        Testing multiplication operator.
        """
        def inner_pipe(data):
            res = data * PipeConstant.from_float(5)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i * 5 for i in range(40)])

    def test_mul_reverse(self):
        """
        Testing mutiplication reverse operator.
        """
        def inner_pipe(data):
            res = PipeConstant.from_float(5) * data
            return res

        self.run_pipe(inner_pipe, list(range(40)), [5 * i for i in range(40)])
