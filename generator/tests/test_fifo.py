import struct
from unittest import TestCase

from myhdl import Signal, ResetSignal, block, always, delay, instance, instances

from common import data_desc
from generator.config import Config
from common.packed_struct import BitVector
from generator.ccip import CcipClData
from generator.fifo import byte_fifo, ByteFifoProducer, ByteFifoConsumer
from utils import num


class Test(TestCase):
    def test_byte_fifo(self):
        # Hacky config to get system_size field filled
        config = Config.from_dict({
            'method': {
                'A': [],
                'b': [],
                'c': []
            },
            'components': [0, 1]
        })

        host_byte_array = bytearray(2048)
        input_id = 0
        n = 100
        h = 0.1
        x_start = 0
        y_start = [2, 1]

        data_offset = 0
        data_size = len(data_desc.get_input_desc(config.system_size)) // 8
        while data_offset + data_size < len(host_byte_array):
            input_id = input_id + 1
            print(input_id)
            struct.pack_into('<Iq2qqI', host_byte_array, data_offset,
                             int(n),
                             num.int_from_float(h),
                             *map(num.int_from_float, reversed(y_start)),
                             num.int_from_float(x_start),
                             int(input_id))
            data_offset += data_size
        drop_bytes_constant = len(host_byte_array) - data_offset

        @block
        def testbench():
            clk = Signal(bool(0))
            rst = ResetSignal(True, True, False)

            p = ByteFifoProducer(BitVector(len(CcipClData) * 4).create_instance())
            c = ByteFifoConsumer(BitVector(len(data_desc.get_input_desc(config.system_size))).create_instance())

            fifo = byte_fifo(clk, rst, p, c)

            @always(delay(5))
            def clk_driver():
                clk.next = not clk

            @instance
            def rst_driver():
                rst.next = True
                yield delay(20)
                rst.next = False

            chunk_offset = Signal(0)

            @instance
            def write_chunk():
                yield delay(100)
                while True:
                    yield clk.posedge
                    if p.wr:
                        if not p.full:
                            print("In: %r" % hex(p.data.val))
                            print("Size: %r" % p.data_size.val)
                            p.wr.next = False
                    else:
                        if not p.full:
                            p.data.next = int.from_bytes(host_byte_array[chunk_offset:chunk_offset + 256], "little")
                            if chunk_offset + 512 <= len(host_byte_array):
                                chunk_offset.next += 256
                            else:
                                chunk_offset.next = 0
                            if chunk_offset >= len(host_byte_array) - 256:
                                p.data_size.next = 256 - drop_bytes_constant
                            else:
                                p.data_size.next = 256

                            p.wr.next = True

            @always(clk.posedge)
            def read_data():
                c.rd.next = True
                if c.rd and not c.empty:
                    print("Out: %r" % hex(c.data.val))
                    (n, h, *y, x, id) = struct.unpack_from('<Iq2qqI', int.to_bytes(int(c.data.val), data_size, "little", signed=False), 0)

                    print({
                        'x': num.to_float(x),
                        'y': list(map(num.to_float, reversed(y))),
                        'id': id
                    })

            return instances()

        tb = testbench()
        tb.config_sim(trace=True)
        tb.run_sim(10000)
