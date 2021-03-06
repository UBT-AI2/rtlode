from typing import Dict
from unittest import TestCase

from myhdl import block, Signal, ResetSignal, always, delay, StopSimulation, instances

from framework.pipeline import PipeInput, PipeOutput, Pipe, PipeSignal
from utils import num


class PipeTestCase(TestCase):
    def run_pipe(self, inner_pipe, input_data, output_data, valid_cycles=5, busy_cycles=20, busy_init=False) -> Dict:
        assert len(input_data) == len(output_data)

        stats = None

        @block
        def testbench():
            clk = Signal(bool(0))
            rst = ResetSignal(False, True, False)

            in_valid = Signal(bool(0))
            in_signal = Signal(num.get_default_type().create(input_data[0]))

            out_busy = Signal(bool(False))

            data_in = PipeInput(in_valid, value=PipeSignal(num.get_default_type(), in_signal))
            res = inner_pipe(data_in.value)
            data_out = PipeOutput(out_busy, res=res)
            pipe = Pipe(data_in, data_out)

            nonlocal stats
            stats = pipe.get_stats()

            pipe_inst = pipe.create(clk, rst)

            @always(delay(10))
            def clk_driver():
                clk.next = not clk

            in_counter = Signal(num.UnsignedIntegerNumberType(32).create(1))
            valid_counter = Signal(num.UnsignedIntegerNumberType(32).create())

            in_valid.next = True

            @always(clk.posedge)
            def input_driver():
                if in_valid and not data_in.pipe_busy:
                    in_counter.next = in_counter + 1
                    in_signal.next = num.get_default_type().create(input_data[min(in_counter, len(input_data) - 1)])
                if valid_counter == valid_cycles:
                    in_valid.next = not in_valid
                    valid_counter.next = 0
                else:
                    valid_counter.next = valid_counter + 1

            busy_counter = Signal(num.UnsignedIntegerNumberType(32).create())
            out_counter = Signal(num.UnsignedIntegerNumberType(32).create(0))

            @always(clk.posedge)
            def output_driver():
                if data_out.pipe_valid and not out_busy:
                    out_counter.next += 1
                    self.assertEqual(num.get_default_type().create_constant(output_data[out_counter]), data_out.res)
                if busy_counter >= busy_cycles:
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
