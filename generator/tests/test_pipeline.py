from framework.pipeline import PipeConstant, Register
from framework.pipeline_elements import add, mul, sub, negate
from generator.tests.helper import PipeTestCase


class TestPipe(PipeTestCase):
    """
    Things to test:
        - PipeOutput with multiple results from different stages
        - Pipe behaviour without any stage
    """

    def test_reg(self):
        """
        Basic pipeline test, testing if data is correctly passed trough two registers.
        """
        def inner_pipe(data):
            reg1 = Register(data)
            reg2 = Register(reg1)
            return reg2

        self.run_pipe(inner_pipe, list(range(40)), list(range(40)))

    def test_simple(self):
        """
        Basic pipeline test, testing creation and function of a simple 2 node pipeline.
        """
        def inner_pipe(data):
            add1 = add(data, PipeConstant.from_float(3))
            mul1 = mul(add1, data)
            return mul1

        self.run_pipe(inner_pipe, list(range(40)), [(i + 3) * i for i in range(40)])

    def test_node_operator(self):
        """
        Testing operators of nodes.
        """
        def inner_pipe(data):
            res_add = data + PipeConstant.from_float(5)
            res = res_add * PipeConstant.from_float(4)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [(i + 5) * 4 for i in range(40)])

    def test_add(self):
        """
        Testing addition.
        """
        def inner_pipe(data):
            res = add(data, PipeConstant.from_float(5))
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i + 5 for i in range(40)])

    def test_add_operator(self):
        """
        Testing addition operator.
        """
        def inner_pipe(data):
            res = data + PipeConstant.from_float(5)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i + 5 for i in range(40)])

    def test_add_reverse_operator(self):
        """
        Testing addition reverse operator.
        """
        def inner_pipe(data):
            res = PipeConstant.from_float(5) + data
            return res

        self.run_pipe(inner_pipe, list(range(40)), [5 + i for i in range(40)])

    def test_sub(self):
        """
        Testing substraction.
        """
        def inner_pipe(data):
            res = sub(data, PipeConstant.from_float(5))
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i - 5 for i in range(40)])

    def test_sub_operator(self):
        """
        Testing substraction operator.
        """
        def inner_pipe(data):
            res = data - PipeConstant.from_float(5)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i - 5 for i in range(40)])

    def test_sub_reverse_operator(self):
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

        self.run_pipe(inner_pipe, list(range(40)), [-i for i in range(40)])

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

    def test_mul_by_shift_left(self):
        """
        Testing multiplication with constant factor on base 2 greater than 1 to test the shift left implementation.
        """
        def inner_pipe(data):
            mul1 = mul(data, PipeConstant.from_float(2))
            add1 = add(mul1, PipeConstant.from_float(3))
            return add1

        self.run_pipe(inner_pipe, list(range(40)), [(i * 2) + 3 for i in range(40)])

    def test_mul_by_shift_right(self):
        """
        Testing multiplication with constant factor on base 2 less than 1 to test the shift right implementation.
        """
        def inner_pipe(data):
            mul1 = mul(data, PipeConstant.from_float(0.5))
            add1 = add(mul1, PipeConstant.from_float(3))
            return add1

        self.run_pipe(inner_pipe, list(range(40)), [(i * 0.5) + 3 for i in range(40)])

    def test_mul(self):
        """
        Testing multiplication with constant factor on base 2 less than 1 to test the shift right implementation.
        """
        def inner_pipe(data):
            add1 = add(data, PipeConstant.from_float(3))
            mul1 = mul(add1, data)
            return mul1

        self.run_pipe(inner_pipe, list(range(40)), [(i + 3) * i for i in range(40)])

    def test_mul_operator(self):
        """
        Testing multiplication operator.
        """
        def inner_pipe(data):
            res = data * PipeConstant.from_float(5)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i * 5 for i in range(40)])

    def test_mul_reverse_operator(self):
        """
        Testing mutiplication reverse operator.
        """
        def inner_pipe(data):
            res = PipeConstant.from_float(5) * data
            return res

        self.run_pipe(inner_pipe, list(range(40)), [5 * i for i in range(40)])

    def test_comb_node_last(self):
        """
        Testing what happens if comb nodes is last node in pipe.
        """
        def inner_pipe(data):
            add1 = add(data, PipeConstant.from_float(3))
            mul1 = mul(add1, PipeConstant.from_float(2))
            return mul1

        self.run_pipe(inner_pipe, list(range(40)), [(i + 3) * 2 for i in range(40)])

    def test_comb_node_double(self):
        """
        Testing what happens if two comb nodes are after each other.
        """
        def inner_pipe(data):
            mul1 = mul(data, PipeConstant.from_float(4))
            mul2 = mul(mul1, PipeConstant.from_float(0.5))
            res = add(mul2, data)
            return res

        self.run_pipe(inner_pipe, list(range(40)), [(i * 4 * 0.5) + i for i in range(40)])

    def test_comb_node_only(self):
        """
        Testing what happens if comb nodes is the only node in pipe.
        """
        def inner_pipe(data):
            mul1 = mul(data, PipeConstant.from_float(2))
            return mul1

        stats = self.run_pipe(inner_pipe, list(range(40)), [i * 2 for i in range(40)])
        self.assertEqual(1, stats['nbr_stages'])

    def test_unconnected_node(self):
        """
        Testing what happens if comb nodes is the only node in pipe.
        """
        def inner_pipe(data):
            add1 = add(data, PipeConstant.from_float(4))
            add2 = add(add1, PipeConstant.from_float(2))
            mul1 = mul(add1, PipeConstant.from_float(2))
            return mul1

        stats = self.run_pipe(inner_pipe, list(range(40)), [(i + 4) * 2 for i in range(40)])
        self.assertEqual(1, stats['by_type']['add'])

    def test_register_reuse(self):
        """
        Testing if registers are reused if two nodes need the same signal in later stage.
        """
        def inner_pipe(data):
            add1 = add(data, PipeConstant.from_float(1))
            add2 = add(add1, PipeConstant.from_float(1))
            add3 = add(add2, PipeConstant.from_float(1))
            add4 = add(add3, PipeConstant.from_float(1))
            add5 = add(add4, PipeConstant.from_float(1))
            add6 = add(add5, PipeConstant.from_float(1))
            add7 = add(add6, PipeConstant.from_float(1))
            mul1 = mul(data, add7)
            mul2 = mul(data, add6)
            res = add(mul1, mul2)
            return res

        stats = self.run_pipe(inner_pipe, list(range(40)), [(i + 7) * i + (i + 6) * i for i in range(40)])
        self.assertEqual(8, stats['by_type']['reg'])
