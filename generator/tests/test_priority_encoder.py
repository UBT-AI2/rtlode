from unittest import TestCase

from myhdl import block, delay, Signal, intbv, instance, instances, StopSimulation

from generator.priority_encoder import priority_encoder_one_hot


class TestPriorityEncoder(TestCase):
    datawidth = 8
    dataset = {
        0b10101010: (0b10000000, 7),
        0b00000000: (0b00000000, 0),
        0b00101010: (0b00100000, 5),
        0b00000001: (0b00000001, 0),
    }

    def test_out_vec(self):
        @block
        def testbench():
            in_val = Signal(intbv(0)[self.datawidth:])
            out_val = Signal(intbv(0)[self.datawidth:])

            dut = priority_encoder_one_hot(in_val, out_val)

            @instance
            def input_driver():
                for in_data, (out_data, _) in self.dataset.items():
                    in_val.next = in_data
                    yield delay(10)
                    self.assertEqual(out_data, out_val)
                raise StopSimulation()

            return instances()

        tb = testbench()
        # tb.config_sim(trace=True)
        tb.run_sim()

    def test_out_index(self):
        @block
        def testbench():
            in_val = Signal(intbv(0)[self.datawidth:])
            out_val = Signal(intbv(0)[self.datawidth:])
            index = Signal(intbv(0)[self.datawidth:])

            dut = priority_encoder_one_hot(in_val, out_val, index)

            @instance
            def input_driver():
                for in_data, (_, index_data) in self.dataset.items():
                    in_val.next = in_data
                    yield delay(10)
                    self.assertEqual(index_data, index)
                raise StopSimulation()

            return instances()

        tb = testbench()
        # tb.config_sim(trace=True)
        tb.run_sim()
