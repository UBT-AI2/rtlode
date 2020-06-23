from generator.pipeline_elements import add, mul, sub, reduce_sum, negate
from generator.tests.helper import PipeTestCase
from utils import num


class TestPipe(PipeTestCase):
    """
    Things to test:
        - PipeOutput with multiple results from different stages
        - Pipe behaviour without any stage
    """

    def test_simple(self):
        """
        Basic pipeline test, testing creation and function of a simple 2 node pipeline.
        """
        def inner_pipe(data):
            add1 = add(data, num.int_from_float(3))
            mul1 = mul(add1, data)
            return mul1

        self.run_pipe(inner_pipe, list(range(40)), [(i + 3) * i for i in range(40)])

    def test_add(self):
        """
        Testing addition.
        """
        def inner_pipe(data):
            res = add(data, num.int_from_float(5))
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i + 5 for i in range(40)])

    def test_sub(self):
        """
        Testing substraction.
        """
        def inner_pipe(data):
            res = sub(data, num.int_from_float(5))
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i - 5 for i in range(40)])

    def test_negate(self):
        """
        Testing substraction.
        """
        def inner_pipe(data):
            res = negate(data)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [-i for i in range(40)])

    def test_mul_only_constants(self):
        """
        Testing multiplication with two constants.
        """
        def inner_pipe(data):
            mul1 = mul(num.int_from_float(2), num.int_from_float(3))
            add1 = add(data, mul1)
            return add1

        self.run_pipe(inner_pipe, list(range(40)), [i + 6 for i in range(40)])

    def test_mul_by_constant(self):
        """
        Testing multiplication with constant factor.
        """
        def inner_pipe(data):
            mul1 = mul(data, num.int_from_float(3))
            add1 = add(mul1, num.int_from_float(3))
            return add1

        self.run_pipe(inner_pipe, list(range(40)), [(i * 3) + 3 for i in range(40)])

    def test_mul_by_shift_left(self):
        """
        Testing multiplication with constant factor on base 2 greater than 1 to test the shift left implementation.
        """
        def inner_pipe(data):
            mul1 = mul(data, num.int_from_float(2))
            add1 = add(mul1, num.int_from_float(3))
            return add1

        self.run_pipe(inner_pipe, list(range(40)), [(i * 2) + 3 for i in range(40)])

    def test_mul_by_shift_right(self):
        """
        Testing multiplication with constant factor on base 2 less than 1 to test the shift right implementation.
        """
        def inner_pipe(data):
            mul1 = mul(data, num.int_from_float(0.5))
            add1 = add(mul1, num.int_from_float(3))
            return add1

        self.run_pipe(inner_pipe, list(range(40)), [(i * 0.5) + 3 for i in range(40)])

    def test_mul(self):
        """
        Testing multiplication with constant factor on base 2 less than 1 to test the shift right implementation.
        """
        def inner_pipe(data):
            add1 = add(data, num.int_from_float(3))
            mul1 = mul(add1, data)
            return mul1

        self.run_pipe(inner_pipe, list(range(40)), [(i + 3) * i for i in range(40)])

    def test_reduce_sum_even(self):
        """
        Testing the reduce_sum pipeline element.
        """
        def inner_pipe(data):
            res = reduce_sum([data for _ in range(4)])
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i * 4 for i in range(40)])

    def test_reduce_sum_odd(self):
        """
        Testing the reduce_sum pipeline element.
        """
        def inner_pipe(data):
            res = reduce_sum([data for _ in range(5)])
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i * 5 for i in range(40)])

    def test_reduce_sum_len1(self):
        """
        Testing the reduce_sum pipeline element with len 1.
        """
        def inner_pipe(data):
            val = reduce_sum([data])
            res = add(val, 0)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i for i in range(40)])

    def test_comb_node_last(self):
        """
        Testing what happens if comb nodes is last node in pipe.
        """
        def inner_pipe(data):
            add1 = add(data, num.int_from_float(3))
            mul1 = mul(add1, num.int_from_float(2))
            return mul1

        self.run_pipe(inner_pipe, list(range(40)), [(i + 3) * 2 for i in range(40)])

    def test_comb_node_double(self):
        """
        Testing what happens if two comb nodes are after each other.
        """
        def inner_pipe(data):
            mul1 = mul(data, num.int_from_float(4))
            mul2 = mul(mul1, num.int_from_float(0.5))
            res = add(mul2, data)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [(i * 4 * 0.5) + i for i in range(40)])

    def test_comb_node_only(self):
        """
        Testing what happens if comb nodes is the only node in pipe.
        """
        def inner_pipe(data):
            mul1 = mul(data, num.int_from_float(2))
            return mul1

        stats = self.run_pipe(inner_pipe, list(range(40)), [i * 2 for i in range(40)])
        self.assertEqual(1, stats['nbr_stages'])

    def test_unconnected_node(self):
        """
        Testing what happens if comb nodes is the only node in pipe.
        """
        def inner_pipe(data):
            add1 = add(data, num.int_from_float(4))
            add2 = add(add1, num.int_from_float(2))
            mul1 = mul(add1, num.int_from_float(2))
            return mul1

        stats = self.run_pipe(inner_pipe, list(range(40)), [(i + 4) * 2 for i in range(40)])
        self.assertEqual(1, stats['by_type']['add'])

    def test_register_reuse(self):
        """
        Testing if registers are reused if two nodes need the same signal in later stage.
        """
        def inner_pipe(data):
            add1 = add(data, num.int_from_float(1))
            add2 = add(add1, num.int_from_float(1))
            add3 = add(add2, num.int_from_float(1))
            add4 = add(add3, num.int_from_float(1))
            add5 = add(add4, num.int_from_float(1))
            add6 = add(add5, num.int_from_float(1))
            add7 = add(add6, num.int_from_float(1))
            mul1 = mul(data, add7)
            mul2 = mul(data, add6)
            res = add(mul1, mul2)
            return res

        stats = self.run_pipe(inner_pipe, list(range(40)), [(i + 7) * i + (i + 6) * i for i in range(40)])
        self.assertEqual(8, stats['by_type']['reg'])
