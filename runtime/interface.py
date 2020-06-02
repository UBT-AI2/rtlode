import math
from typing import List, Dict

import struct
from opae import fpga

from common import data_desc
from utils import num

CHUNK_SIZE = 256


class Solver:
    def __init__(self, config, buffer_size):
        """
        Interface to a already loaded solver described by config.
        :param config: configuration of solver (just load it from the .slv)
        :param buffer_size: buffer size in bytes to be used for data input / output,
                            the system must support ram pages of this size (without hugepage typically max 4096 bytes)
        """
        self._config = config
        self._system_size = len(config['problem']['components'])
        self._csr_addresses = config['build_info']['csr_addresses']
        # Shift all addresses
        for key, val in self._csr_addresses.items():
            self._csr_addresses[key] = val << 2
        # Buffer handling
        self._buffer_size = buffer_size
        self._input_buffer = None
        self._output_buffer = None
        self._current_input_id = 0

        # Input buffer positions
        self._input_data_offset = 0
        self._input_data_chunk = 0

        # Input buffer positions
        self._output_data_offset = 0
        self._output_data_chunk = 0

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

        self.stop()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fpga.__exit__(exc_type, exc_val, exc_tb)
        self._handle = None

    def start(self):
        """
        Start calculation on the fpga.
        Calculates the chunk_size and writes it to the fpga. Sets the enb bit on the fpga.
        :return:
        """
        nbr_chunks = int(math.ceil((self._input_data_chunk + self._input_data_offset) / CHUNK_SIZE))
        self.buffer_size = nbr_chunks

        self.enb = True

    def stop(self):
        """
        Stop calculation on the fpga.
        Resets system to allow a restart.
        :return:
        """
        self.enb = False

        self._input_data_offset = 0
        self._input_data_chunk = 0

        self._output_data_offset = 0
        self._output_data_chunk = 0

    def input_full(self) -> bool:
        """
        Returns true if all possible inputs of given buffer size are used.
        You can't add more inputs. Either increase buffer size or restart the solver with new input.
        :return: true if input is full
        """
        input_data_size = len(data_desc.get_input_desc(self._system_size)) // 8
        return (self._input_data_chunk + self._input_data_offset) + input_data_size > self._buffer_size

    def add_input(self, x_start: float, y_start: List[float], h: int, n: int) -> int:
        """
        Adds a given input dataset to the fpga communication buffer.
        :param x_start: solver input
        :param y_start: solver input
        :param h: solver input
        :param n: solver input
        :return: id referring to given dataset, can be used to match results
        """
        assert len(y_start) == self._system_size
        assert not self.input_full()

        self._current_input_id = self._current_input_id + 1

        packed_data = data_desc.pack_input_data(self._system_size, {
            'id': int(self._current_input_id),
            'x_start': num.int_from_float(x_start),
            'y_start': list(map(num.int_from_float, reversed(y_start))),
            'h': num.int_from_float(h),
            'n': int(n)
        })
        packed_data_len = len(packed_data)

        offset = self._input_data_chunk + self._input_data_offset
        for i in range(packed_data_len):
            self._input_buffer[offset + i] = packed_data[i]

        self._input_data_offset += packed_data_len
        if CHUNK_SIZE - self._input_data_offset < packed_data_len:
            self._input_data_chunk += CHUNK_SIZE
            self._input_data_offset = 0

        return self._current_input_id

    def fetch_output(self) -> Dict:
        """
        Return the solver outputs one after another. The order is the output order of the solver.
        :return: dictionary with id, x, y
        """
        packed_data_len = len(data_desc.get_output_desc(self._system_size)) // 8

        offset = self._output_data_offset + self._output_data_chunk
        packed_data = self._output_buffer[offset:offset + packed_data_len]

        unpacked_data = data_desc.unpack_output_data(self._system_size, bytes(packed_data))

        self._output_data_offset += packed_data_len
        if CHUNK_SIZE - self._output_data_offset < packed_data_len:
            self._output_data_chunk += CHUNK_SIZE
            self._output_data_offset = 0

        return {
            'id': unpacked_data['id'],
            'x': num.to_float(unpacked_data['x']),
            'y': list(map(num.to_float, reversed(unpacked_data['y'])))
        }

    @property
    def buffer_size(self):
        return self._handle.read_csr64(self._csr_addresses['buffer_size'])

    @buffer_size.setter
    def buffer_size(self, value):
        self._handle.write_csr64(self._csr_addresses['buffer_size'], value)

    @property
    def enb(self):
        return self._handle.read_csr64(self._csr_addresses['enb'])

    @enb.setter
    def enb(self, value):
        self._handle.write_csr64(self._csr_addresses['enb'], value)

    @property
    def fin(self):
        return self._handle.read_csr64(self._csr_addresses['fin'])
