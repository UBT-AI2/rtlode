from unittest import TestCase

from myhdl import Signal, ResetSignal, delay, always, intbv, instances, block

from generator.cdc_utils import AsyncFifoProducer, AsyncFifoConsumer, async_fifo


class Test(TestCase):
    def test_async_fifo(self):
        @block
        def testbench():
            fifo_p = AsyncFifoProducer(clk=Signal(bool(0)), rst=ResetSignal(False, True, False), data=Signal(intbv(0)))
            fifo_c = AsyncFifoConsumer(clk=Signal(bool(0)), rst=ResetSignal(False, True, False), data=Signal(intbv(0)))

            fifo = async_fifo(fifo_p, fifo_c, buffer_size_bits=4)

            @always(delay(10))
            def p_clk():
                fifo_p.clk.next = not fifo_p.clk

            @always(fifo_p.clk.posedge)
            def p_write():
                if not fifo_p.full:
                    fifo_p.data.next = fifo_p.data.next + 1
                    fifo_p.wr.next = True
                else:
                    fifo_p.wr.next = False

            @always(fifo_p.clk.posedge)
            def p_diag():
                print('Full? %s' % fifo_p.full)

            @always(delay(25))
            def c_clk():
                fifo_c.clk.next = not fifo_c.clk

            @always(fifo_c.clk.posedge)
            def c_read():
                if fifo_c.rd:
                    print("CR: %r" % fifo_c.data)
                if not fifo_c.empty:
                    fifo_c.rd.next = True
                else:
                    fifo_c.rd.next = False

            return instances()

        tb = testbench()
        # tb.config_sim(trace=True)
        tb.run_sim(1000)
        tb.quit_sim()
