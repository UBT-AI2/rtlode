from unittest import TestCase

from myhdl import Signal, ResetSignal, delay, always, intbv, instances, block, instance

from framework.fifo import FifoProducer, FifoConsumer, fifo


class Test(TestCase):
    def test_fifo(self):
        @block
        def testbench():
            clk = Signal(bool(0))
            rst = ResetSignal(False, True, False)

            fifo_p = FifoProducer(data=Signal(intbv(0)))
            fifo_c = FifoConsumer(data=Signal(intbv(0)))

            fifo_inst = fifo(clk, rst, fifo_p, fifo_c, buffer_size_bits=2)

            @always(delay(5))
            def clk_driver():
                clk.next = not clk

            @instance
            def input_driver():
                fifo_p.data.next = 0
                while True:
                    yield clk.posedge
                    if not fifo_p.full:
                        fifo_p.data.next = fifo_p.data + 1
                        fifo_p.wr.next = True
                    yield clk.posedge
                    fifo_p.wr.next = False

            @instance
            def output_driver():
                fifo_c.rd.next = True
                while True:
                    yield clk.posedge
                    if fifo_c.rd and not fifo_c.empty:
                        print("Data: %r" % fifo_c.data)

            return instances()

        tb = testbench()
        tb.config_sim(trace=True)
        tb.run_sim(500)
        tb.quit_sim()
