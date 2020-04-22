from typing import List
from unittest import TestCase

from myhdl import Signal, ResetSignal, delay, always, intbv, instances, block, always_seq

from common.config import Config
from common.data_desc import get_input_desc, get_output_desc
from common.packed_struct import BitVector
from generator.cdc_utils import FifoProducer, FifoConsumer, async_fifo
from generator.dispatcher import dispatcher
from utils import num

current_input_id = 0


def create_input_data(x_start: float, y_start: List[float], h: int, n: int):
    global current_input_id
    system_size = len(y_start)

    input_desc = get_input_desc(system_size)
    input_data = input_desc.create_write_instance()

    input_data.x_start.next = num.from_float(x_start)
    for i in range(system_size):
        input_data.y_start[i].next = num.from_float(y_start[i])
    input_data.h.next = num.from_float(h)
    input_data.n.next = int(n)

    current_input_id = current_input_id + 1
    input_data.id.next = int(current_input_id)

    input_data.update()
    input_packed = input_data.packed()
    return int(input_packed)


class Test(TestCase):
    def test_solver(self):

        @block
        def testbench():
            system_size = 1

            clk = Signal(bool(0))
            reset = ResetSignal(False, True, False)
            usr_clk = Signal(bool(0))
            usr_reset = ResetSignal(False, True, False)

            input_desc_vec = BitVector(len(get_input_desc(system_size)))
            output_desc_vec = BitVector(len(get_output_desc(system_size)))

            in_fifo_p = FifoProducer(clk, reset, input_desc_vec.create_instance())
            in_fifo_c = FifoConsumer(usr_clk, usr_reset, input_desc_vec.create_instance())
            in_fifo = async_fifo(in_fifo_p, in_fifo_c, buffer_size_bits=4)

            out_fifo_p = FifoProducer(usr_clk, usr_reset, output_desc_vec.create_instance())
            out_fifo_c = FifoConsumer(clk, reset, output_desc_vec.create_instance())
            out_fifo = async_fifo(out_fifo_p, out_fifo_c, buffer_size_bits=4)

            disp_inst = dispatcher(Config.from_dict(
                {'method': {'A': [[]], 'b': [1], 'c': [1]}, 'x': 0, 'y': [2], 'h': 0.1, 'n': 20,
                 'components': ['2 * y[0]']}
            ), data_in=in_fifo_c, data_out=out_fifo_p)

            parsed_output_data = get_output_desc(system_size).create_read_instance(out_fifo_c.data)

            in_fifo_p.data.next = create_input_data(0, [2], 0.1, 20)
            in_fifo_p.data._update()

            @always(delay(10))
            def clk_driver():
                clk.next = not clk

            @always(delay(43))
            def usr_clk_driver():
                usr_clk.next = not usr_clk

            @always(in_fifo_p.clk.posedge)
            def p_write():
                in_fifo_p.wr.next = True
                if in_fifo_p.wr and not in_fifo_p.full:
                    in_fifo_p.data.next = create_input_data(0, [2], 0.1, 20)

            @always_seq(out_fifo_c.clk.posedge, reset=None)
            def c_read():
                out_fifo_c.rd.next = True
                if out_fifo_c.rd and not out_fifo_c.empty:
                    y = []
                    for el in parsed_output_data.y:
                        y.append(num.to_float(el))

                    print("Out: %r" % {
                        'x': num.to_float(parsed_output_data.x),
                        'y': y,
                        'id': parsed_output_data.id
                    })

            return instances()

        tb = testbench()
        tb.config_sim(trace=True)
        tb.run_sim(500000)
