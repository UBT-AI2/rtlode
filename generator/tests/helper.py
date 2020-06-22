from typing import Dict
from unittest import TestCase

from myhdl import block, Signal, ResetSignal, always, delay, StopSimulation, instances

from generator.pipeline import PipeInput, PipeOutput, Pipe
from utils import num


class PipeTestCase(TestCase):
    def run_pipe(self, inner_pipe, input_data, output_data) -> Dict:
        assert len(input_data) == len(output_data)

        stats = None

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

            nonlocal stats
            stats = pipe.get_stats()

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

        print(stats)
        return stats
