from unittest import TestCase

from myhdl import Signal, block, ResetSignal, instances, delay, always, StopSimulation

from generator.pipeline import PipeInput, PipeOutput, Pipe
from generator.pipeline_elements import add, mul
from utils import num


class TestPipe(TestCase):
    def test_create(self):
        """
        Basic pipeline test, testing creation and function of a simple 2 node pipeline.
        """
        @block
        def testbench():
            clk = Signal(bool(0))
            rst = ResetSignal(False, True, False)

            in_valid = Signal(bool(0))
            in_signal = Signal(num.default())

            out_busy = Signal(bool(0))

            data_in = PipeInput(in_valid, a=in_signal)
            add1 = add(data_in.a, num.int_from_float(3))
            mul1 = mul(add1, data_in.a)
            data_out = PipeOutput(out_busy, res=mul1)
            pipe = Pipe(data_in, data_out).create(clk, rst)

            @always(delay(10))
            def clk_driver():
                clk.next = not clk

            in_counter = Signal(num.integer(0))

            @always(clk.posedge)
            def input_driver():
                in_valid.next = True
                if not data_in.pipe_busy:
                    in_counter.next = in_counter + 1
                    in_signal.next = num.from_float(in_counter)
                if in_counter == 40:
                    raise StopSimulation()

            busy_counter = Signal(num.integer())

            out_counter = Signal(num.integer(0))
            reg_busy = Signal(bool(0))

            @always(clk.posedge)
            def output_driver():
                if not out_busy:
                    reg_busy.next = False

                if data_out.pipe_valid and not reg_busy:
                    out_counter.next += 1
                    self.assertEqual(num.int_from_float((out_counter + 3) * out_counter), data_out.res)
                    print(data_out.res)
                    if out_busy:
                        reg_busy.next = True
                if busy_counter == 10:
                    out_busy.next = not out_busy
                    busy_counter.next = 0
                else:
                    busy_counter.next = busy_counter + 1

            return instances()

        tb = testbench()
        tb.config_sim(trace=True)
        tb.run_sim()
