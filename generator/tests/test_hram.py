from unittest import TestCase

import struct
from myhdl import block, Signal, ResetSignal, always, delay, instances, instance

from common import data_desc
from common.config import Config
from common.packed_struct import BitVector
from generator.ccip import CcipClData
from generator.cdc_utils import FifoProducer
from generator.hram import data_chunk_parser
from utils import num


class Test(TestCase):
    def test_data_chunk_parser(self):
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

        offset = 0
        data_size = len(data_desc.get_input_desc(config.system_size)) // 8
        while offset + data_size < len(host_byte_array):
            input_id = input_id + 1
            struct.pack_into('<Iq2qqI', host_byte_array, offset,
                             int(n),
                             num.int_from_float(h),
                             *map(num.int_from_float, reversed(y_start)),
                             num.int_from_float(x_start),
                             int(input_id))
            offset += data_size
        drop_bytes_constant = len(host_byte_array) - offset

        @block
        def testbench():
            clk = Signal(bool(0))
            rst = ResetSignal(False, True, False)

            data_out = FifoProducer(clk, rst,
                                    BitVector(len(data_desc.get_input_desc(config.system_size))).create_instance())
            chunk_in = FifoProducer(clk, rst, BitVector(len(CcipClData) * 4).create_instance())
            input_ack_id = Signal(num.integer())
            drop_rest = Signal(bool(0))
            drop_bytes = Signal(num.integer(drop_bytes_constant))

            parser = data_chunk_parser(config, data_out, chunk_in, input_ack_id, drop_rest, drop_bytes)

            @always(delay(5))
            def clk_driver():
                clk.next = not clk

            chunk_offset = Signal(0)

            @instance
            def write_chunk():
                yield delay(100)
                while True:
                    yield clk.posedge
                    if chunk_in.wr:
                        if not chunk_in.full:
                            chunk_in.wr.next = False
                    else:
                        chunk_in.data.next = int.from_bytes(host_byte_array[chunk_offset:chunk_offset + 256], "big")
                        if chunk_offset + 256 < len(host_byte_array):
                            chunk_offset.next += 256
                            drop_rest.next = False
                        else:
                            drop_rest.next = True
                            chunk_offset.next = 0
                        yield delay(200)
                        chunk_in.wr.next = True

            @always(clk.posedge)
            def read_data():
                data_out.full.next = False
                if data_out.wr:
                    print("(id, data): (%r, %r)" % (input_ack_id, data_out.data))

            return instances()

        tb = testbench()
        tb.config_sim(trace=True)
        tb.run_sim(100000)
