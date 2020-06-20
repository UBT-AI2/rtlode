from unittest import TestCase

from myhdl import Signal, block, ResetSignal, instances, delay, always, StopSimulation

from generator.pipeline import PipeInput, PipeOutput, Pipe
from generator.pipeline_elements import add, mul, sub, reduce_sum
from utils import num


class TestPipe(TestCase):
    def test_simple(self):
        """
        Basic pipeline test, testing creation and function of a simple 2 node pipeline.
        """
        def inner_pipe(data):
            add1 = add(data, num.int_from_float(3))
            mul1 = mul(add1, data)
            return mul1

        self.run_test(inner_pipe, list(range(40)), [(i + 3) * i for i in range(40)])

    def test_add(self):
        """
        Testing addition.
        """
        def inner_pipe(data):
            res = add(data, num.int_from_float(5))
            return res

        self.run_test(inner_pipe, list(range(40)), [i + 5 for i in range(40)])

    def test_sub(self):
        """
        Testing substraction.
        """
        def inner_pipe(data):
            res = sub(data, num.int_from_float(5))
            return res

        self.run_test(inner_pipe, list(range(40)), [i - 5 for i in range(40)])

    def test_mul_only_constants(self):
        """
        Testing multiplication with two constants.
        """
        def inner_pipe(data):
            mul1 = mul(num.int_from_float(2), num.int_from_float(3))
            add1 = add(data, mul1)
            return add1

        self.run_test(inner_pipe, list(range(40)), [i + 6 for i in range(40)])

    def test_mul_by_constant(self):
        """
        Testing multiplication with constant factor.
        """
        def inner_pipe(data):
            mul1 = mul(data, num.int_from_float(3))
            add1 = add(mul1, num.int_from_float(3))
            return add1

        self.run_test(inner_pipe, list(range(40)), [(i * 3) + 3 for i in range(40)])

    def test_mul_by_shift_left(self):
        """
        Testing multiplication with constant factor on base 2 greater than 1 to test the shift left implementation.
        """
        def inner_pipe(data):
            mul1 = mul(data, num.int_from_float(2))
            add1 = add(mul1, num.int_from_float(3))
            return add1

        self.run_test(inner_pipe, list(range(40)), [(i * 2) + 3 for i in range(40)])

    def test_mul_by_shift_right(self):
        """
        Testing multiplication with constant factor on base 2 less than 1 to test the shift right implementation.
        """
        def inner_pipe(data):
            mul1 = mul(data, num.int_from_float(0.5))
            add1 = add(mul1, num.int_from_float(3))
            return add1

        self.run_test(inner_pipe, list(range(40)), [(i * 0.5) + 3 for i in range(40)])

    def test_mul(self):
        """
        Testing multiplication with constant factor on base 2 less than 1 to test the shift right implementation.
        """
        def inner_pipe(data):
            add1 = add(data, num.int_from_float(3))
            mul1 = mul(add1, data)
            return mul1

        self.run_test(inner_pipe, list(range(40)), [(i + 3) * i for i in range(40)])

    def test_reduce_sum(self):
        """
        Testing the reduce_sum pipeline element.
        """
        def inner_pipe(data):
            res = reduce_sum([data for _ in range(5)])
            return res

        self.run_test(inner_pipe, list(range(40)), [i * 5 for i in range(40)])

    def test_reduce_sum_len1(self):
        """
        Testing the reduce_sum pipeline element with len 1.
        """
        def inner_pipe(data):
            val = reduce_sum([data])
            res = add(val, 0)
            return res

        self.run_test(inner_pipe, list(range(40)), [i for i in range(40)])

    def test_comb_node_last(self):
        """
        Testing what happens if comb nodes is last node in pipe.
        """
        def inner_pipe(data):
            add1 = add(data, num.int_from_float(3))
            mul1 = mul(add1, num.int_from_float(2))
            return mul1

        self.run_test(inner_pipe, list(range(40)), [(i + 3) * 2 for i in range(40)])

    def test_comb_node_only(self):
        """
        Testing what happens if comb nodes is the only node in pipe.
        """
        def inner_pipe(data):
            mul1 = mul(data, num.int_from_float(2))
            return mul1

        self.run_test(inner_pipe, list(range(40)), [(i + 3) * 2 for i in range(40)])

    def run_test(self, inner_pipe, input_data, output_data):
        assert len(input_data) == len(output_data)

        @block
        def testbench():
            clk = Signal(bool(0))
            rst = ResetSignal(False, True, False)

            in_valid = Signal(bool(0))
            in_signal = Signal(num.default())

            out_busy = Signal(bool(0))

            data_in = PipeInput(in_valid, value=in_signal)
            res = inner_pipe(data_in.value)
            data_out = PipeOutput(out_busy, res=res)
            pipe = Pipe(data_in, data_out)
            print(pipe.get_stats())
            pipe_inst = pipe.create(clk, rst)

            @always(delay(10))
            def clk_driver():
                clk.next = not clk

            in_counter = Signal(num.integer(0))

            @always(clk.posedge)
            def input_driver():
                in_valid.next = True
                if not data_in.pipe_busy:
                    in_counter.next = in_counter + 1
                    in_signal.next = num.from_float(input_data[min(in_counter, len(input_data) - 1)])

            busy_counter = Signal(num.integer())

            out_counter = Signal(num.integer(0))
            reg_busy = Signal(bool(0))

            @always(clk.posedge)
            def output_driver():
                if not out_busy:
                    reg_busy.next = False

                if data_out.pipe_valid and not reg_busy:
                    out_counter.next += 1
                    self.assertEqual(num.int_from_float(output_data[out_counter]), data_out.res)
                    print(data_out.res)
                    if out_busy:
                        reg_busy.next = True
                if busy_counter == 10:
                    out_busy.next = not out_busy
                    busy_counter.next = 0
                else:
                    busy_counter.next = busy_counter + 1

                if out_counter == len(output_data) - 1:
                    raise StopSimulation()

            return instances()

        tb = testbench()
        # tb.config_sim(trace=True)
        tb.run_sim()
