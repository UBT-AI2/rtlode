from framework.pipeline import PipeConstant
from framework.pipeline_elements import add, mul, negate
from framework.tests.helper import PipeTestCase
from utils import num


class TestPipe(PipeTestCase):
    def run(self, result=None):
        # Run twice for each floating precision
        previous_type = num.get_default_type()
        num.set_default_type(num.FloatingNumberType(num.FloatingPrecision.DOUBLE))
        super().run(result)
        num.set_default_type(num.FloatingNumberType(num.FloatingPrecision.SINGLE))
        super().run(result)
        num.set_default_type(previous_type)

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

    def test_different_valid_cycles(self):
        """
        Testing if pipelines handles different rythms of valid signals correctly.
        Same as in test_pipeline, but floating point elements could be implemented differently.
        """
        def inner_pipe(data):
            add1 = add(data, PipeConstant.from_float(1))
            add2 = add(add1, PipeConstant.from_float(1))
            add3 = add(add2, PipeConstant.from_float(1))
            add4 = add(add3, PipeConstant.from_float(1))
            add5 = add(add4, PipeConstant.from_float(1))
            add6 = add(add5, PipeConstant.from_float(1))
            res = add(add6, PipeConstant.from_float(1))
            return res

        for valid_cycles in range(1, 40):
            self.run_pipe(
                inner_pipe,
                list(range(40)), [i + 7 for i in range(40)],
                valid_cycles=valid_cycles,
                busy_cycles=5 if valid_cycles != 5 else 4
            )

    def test_different_busy_cycles(self):
        """
        Testing if pipelines handles different rythms of busy signals correctly.
        Same as in test_pipeline, but floating point elements could be implemented differently.
        """
        def inner_pipe(data):
            add1 = add(data, PipeConstant.from_float(1))
            add2 = add(add1, PipeConstant.from_float(1))
            add3 = add(add2, PipeConstant.from_float(1))
            add4 = add(add3, PipeConstant.from_float(1))
            add5 = add(add4, PipeConstant.from_float(1))
            add6 = add(add5, PipeConstant.from_float(1))
            res = add(add6, PipeConstant.from_float(1))
            return res

        for busy_cycles in range(1, 100):
            self.run_pipe(
                inner_pipe,
                list(range(40)), [i + 7 for i in range(40)],
                valid_cycles=5 if busy_cycles != 5 else 4,
                busy_cycles=busy_cycles,
                busy_init=False
            )
            self.run_pipe(
                inner_pipe,
                list(range(40)), [i + 7 for i in range(40)],
                valid_cycles=5 if busy_cycles != 5 else 4,
                busy_cycles=busy_cycles,
                busy_init=True
            )
