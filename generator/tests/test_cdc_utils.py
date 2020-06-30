from unittest import TestCase

from myhdl import Signal, ResetSignal, delay, always, intbv, instances, block, instance

from generator.cdc_utils import AsyncFifoProducer, AsyncFifoConsumer, async_fifo


class Test(TestCase):
    def test_async_fifo(self):
        @block
        def testbench():
            fifo_p = AsyncFifoProducer(clk=Signal(bool(0)), rst=ResetSignal(False, True, False), data=Signal(intbv(0)))
            fifo_c = AsyncFifoConsumer(clk=Signal(bool(0)), rst=ResetSignal(False, True, False), data=Signal(intbv(0)))

            fifo = async_fifo(fifo_p, fifo_c, buffer_size_bits=4)

            @always(delay(25))
            def p_clk():
                fifo_p.clk.next = not fifo_p.clk

            @always(fifo_p.clk.posedge)
            def p_write():
                fifo_p.wr.next = True
                if fifo_p.wr and not fifo_p.full:
                    fifo_p.data.next = fifo_p.data.next + 1
                    fifo_p.wr.next = True

            @always(fifo_p.clk.posedge)
            def p_diag():
                print('Full? %s' % fifo_p.full)

            @always(delay(10))
            def c_clk():
                fifo_c.clk.next = not fifo_c.clk

            @instance
            def c_read():
                while True:
                    for _ in range(10):
                        yield fifo_c.clk.posedge
                    fifo_c.rd.next = True
                    yield fifo_c.clk.posedge
                    if fifo_c.rd and not fifo_c.empty:
                        print("CR: %r" % fifo_c.data)
                    fifo_c.rd.next = False

            return instances()

        tb = testbench()
        # tb.config_sim(trace=True)
        tb.run_sim(20000)
        tb.quit_sim()
