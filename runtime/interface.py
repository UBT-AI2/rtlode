import math
from typing import List, Union, Dict

import struct
from opae import fpga

from utils import num


class Solver:

    def __init__(self, config, buffer_size):
        self._config = config
        self._csr_addresses = config['build_info']['csr_addresses']
        # Shift all addresses
        for key, val in self._csr_addresses.items():
            self._csr_addresses[key] = val << 2
        # Buffer handling
        self._buffer_size = buffer_size
        self._input_buffer = None
        self._output_buffer = None
        self._current_input_id = 0
        self._current_output_id = 0

    def __enter__(self):
        # TODO enable guid filter if segfault in opae is fixed
        tokens = fpga.enumerate(type=fpga.ACCELERATOR)  # , guid=self._config['build_info']['uuid'])
        if tokens is None or len(tokens) < 1:
            raise Exception('No usable afu could be found on fpga.')
        self._fpga = fpga.open(tokens[0], fpga.OPEN_SHARED)
        self._handle = self._fpga.__enter__()

        self._input_buffer = fpga.allocate_shared_buffer(self._handle, self._buffer_size)
        self._handle.write_csr64(self._csr_addresses['input_addr'], self._input_buffer.io_address() >> 6)
        self._output_buffer = fpga.allocate_shared_buffer(self._handle, self._buffer_size)
        self._handle.write_csr64(self._csr_addresses['output_addr'], self._output_buffer.io_address() >> 6)

        self._input_data_offset = 0

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fpga.__exit__(exc_type, exc_val, exc_tb)
        self._handle = None

    def input_full(self):
        return self._input_data_offset + 40 <= self.buffer_size

    def add_input(self, x_start: float, y_start: List[float], h: int, n: int) -> int:
        """
        Adds a given input dataset to the fpga communication buffer.
        :param x_start: solver input
        :param y_start: solver input
        :param h: solver input
        :param n: solver input
        :return: id referring to given dataset, can be used to match results
        """
        self._current_input_id = self._current_input_id + 1
        struct.pack_into('<Iq2qqI', self._input_buffer, self._input_data_offset,
                         int(n),
                         num.int_from_float(h),
                         *map(num.int_from_float, reversed(y_start)),
                         num.int_from_float(x_start),
                         int(self._current_input_id))
        self._input_data_offset += 40

        return self._current_input_id

    def start(self):
        buffer_size = int(math.ceil(self._input_data_offset / 256))
        self.buffer_size = buffer_size
        self.buffer_unused_bytes = buffer_size * 256 - self._input_data_offset

        self.enb = True

    # def fetch_output(self) -> Union[None, Dict]:
    #     (*y, x, id) = struct.unpack_from('<2qqI', self._output_buffer, 0)
    #
    #     if id > self._current_output_id:
    #         # New data available
    #         self._current_output_id = self._current_output_id + 1
    #         self.output_ack_id = self._current_output_id
    #         return {
    #             'x': num.to_float(x),
    #             'y': list(map(num.to_float, reversed(y))),
    #             'id': id
    #         }
    #     else:
    #         return None

    @property
    def buffer_size(self):
        return self._handle.read_csr64(self._csr_addresses['buffer_size'])

    @buffer_size.setter
    def buffer_size(self, value):
        self._handle.write_csr64(self._csr_addresses['buffer_size'], value)

    @property
    def buffer_unused_bytes(self):
        return self._handle.read_csr64(self._csr_addresses['buffer_unused_bytes'])

    @buffer_unused_bytes.setter
    def buffer_unused_bytes(self, value):
        self._handle.write_csr64(self._csr_addresses['buffer_unused_bytes'], value)

    @property
    def enb(self):
        return self._handle.read_csr64(self._csr_addresses['enb'])

    @enb.setter
    def enb(self, value):
        self._handle.write_csr64(self._csr_addresses['enb'], value)

    @property
    def fin(self):
        return self._handle.read_csr64(self._csr_addresses['fin'])
