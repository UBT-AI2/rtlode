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
        self.y_start = None
        self.y = None

    def __enter__(self):
        # TODO enable guid filter if segfault in opae is fixed
        tokens = fpga.enumerate(type=fpga.ACCELERATOR)  # , guid=self._config['build_info']['uuid'])
        if tokens is None or len(tokens) < 1:
            raise Exception('No usable afu could be found on fpga.')
        self._fpga = fpga.open(tokens[0], fpga.OPEN_SHARED)
        self._handle = self._fpga.__enter__()

        self.y_start = self._fpga.allocate_shared_buffer(self._handle, self._buffer_size)
        self._handle.write_csr64(self._csr_addresses['y_start_mem_addr'], self.y_start.io_address() >> 6)
        self.y = self._fpga.allocate_shared_buffer(self._handle, self._buffer_size)
        self._handle.write_csr64(self._csr_addresses['y_mem_addr'], self.y.io_address() >> 6)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fpga.__exit__(exc_type, exc_val, exc_tb)
        self._handle = None

    @property
    def h(self):
        return num.to_float(self._handle.read_csr64(self._csr_addresses['h']))

    @h.setter
    def h(self, value):
        self._handle.write_csr64(self._csr_addresses['h'], num.from_float(value))

    @property
    def n(self):
        return self._handle.read_csr64(self._csr_addresses['n'])

    @n.setter
    def n(self, value):
        self._handle.write_csr64(self._csr_addresses['n'], value)

    @property
    def x_start(self):
        return num.to_float(self._handle.read_csr64(self._csr_addresses['x_start']))

    @x_start.setter
    def x_start(self, value):
        self._handle.write_csr64(self._csr_addresses['x_start'], num.from_float(value))

    @property
    def x(self):
        return num.to_float(self._handle.read_csr64(self._csr_addresses['x']))

    @x.setter
    def x(self, value):
        self._handle.write_csr64(self._csr_addresses['x'], num.from_float(value))

    @property
    def enb(self):
        return self._handle.read_csr64(self._csr_addresses['enb'])

    @enb.setter
    def enb(self, value):
        self._handle.write_csr64(self._csr_addresses['enb'], value)

    @property
    def fin(self):
        return self._handle.read_csr64(self._csr_addresses['fin'])

    @fin.setter
    def fin(self, value):
        self._handle.write_csr64(self._csr_addresses['fin'], value)
