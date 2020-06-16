from unittest import TestCase

from myhdl import Signal, block, ResetSignal, instances, delay, always, StopSimulation

from generator.pipeline import PipeInput, PipeOutput, Pipe
from generator.pipeline_elements import Add, Mul
from utils import num


class TestPipe(TestCase):
    def test_create(self):
        @block
        def testbench():
            clk = Signal(bool(0))
            rst = ResetSignal(False, True, False)

            in_valid = Signal(bool(0))
            in_signal = Signal(num.integer())

            out_busy = Signal(bool(0))

            data_in = PipeInput(in_valid, a=in_signal)
            add1 = Add(data_in.a, 3)
            mul1 = Mul(add1, data_in.a)
            data_out = PipeOutput(out_busy, res=mul1)
            pipe = Pipe(data_in, data_out).create(clk, rst)

            @always(delay(10))
            def clk_driver():
                clk.next = not clk

            @always(clk.posedge)
            def input_driver():
                in_valid.next = True
                if not data_in.pipe_busy:
                    in_signal.next = in_signal + 1
                if in_signal == 40:
                    raise StopSimulation()

            busy_counter = Signal(num.integer())

            @always(clk.posedge)
            def output_driver():
                if data_out.pipe_valid:
                    print(data_out.res)
                if busy_counter == 10:
                    out_busy.next = not out_busy
                    busy_counter.next = 0
                else:
                    busy_counter.next = busy_counter + 1

            return instances()

        tb = testbench()
        tb.config_sim(trace=True)
        tb.run_sim()
