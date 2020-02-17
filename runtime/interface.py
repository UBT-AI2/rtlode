from opae import fpga

from utils import num


class Solver:

    def __init__(self, config):
        self._config = config

    def __enter__(self):
        # TODO enable guid filter if segfault in opae is fixed
        tokens = fpga.enumerate(type=fpga.ACCELERATOR)  # , guid=self._config['build_info']['uuid'])
        if tokens is None or len(tokens) < 1:
            raise Exception('No usable afu could be found on fpga.')
        self._fpga = fpga.open(tokens[0], fpga.OPEN_SHARED)
        self._handle = self._fpga.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fpga.__exit__(exc_type, exc_val, exc_tb)
        self._handle = None

    @property
    def h(self):
        # TODO use addresses of config
        return num.to_float(self._handle.read_csr64(0x20 << 2))

    @h.setter
    def h(self, value):
        self._handle.write_csr64(0x20 << 2, num.from_float(value))

    @property
    def n(self):
        # TODO use addresses of config
        return num.to_float(self._handle.read_csr64(0x30 << 2))

    @n.setter
    def n(self, value):
        self._handle.write_csr64(0x30 << 2, num.from_float(value))

    @property
    def x_start(self):
        # TODO use addresses of config
        return num.to_float(self._handle.read_csr64(0x40 << 2))

    @x_start.setter
    def x_start(self, value):
        self._handle.write_csr64(0x40 << 2, num.from_float(value))

    @property
    def y_start_addr(self):
        # TODO use addresses of config
        return self._handle.read_csr64(0x50 << 2)

    @y_start_addr.setter
    def y_start_addr(self, value):
        self._handle.write_csr64(0x50 << 2, value)

    @property
    def y_start_val(self):
        # TODO use addresses of config
        return num.to_float(self._handle.read_csr64(0x60 << 2))

    @y_start_val.setter
    def y_start_val(self, value):
        self._handle.write_csr64(0x60 << 2, num.from_float(value))

    @property
    def x(self):
        # TODO use addresses of config
        return num.to_float(self._handle.read_csr64(0x70 << 2))

    @x.setter
    def x(self, value):
        self._handle.write_csr64(0x70 << 2, num.from_float(value))

    @property
    def y_addr(self):
        # TODO use addresses of config
        return self._handle.read_csr64(0x80 << 2)

    @y_addr.setter
    def y_addr(self, value):
        self._handle.write_csr64(0x80 << 2, value)

    @property
    def y_val(self):
        # TODO use addresses of config
        return num.to_float(self._handle.read_csr64(0x90 << 2))

    @y_val.setter
    def y_val(self, value):
        self._handle.write_csr64(0x90 << 2, num.from_float(value))

    @property
    def enb(self):
        # TODO use addresses of config
        return self._handle.read_csr64(0xA0 << 2)

    @enb.setter
    def enb(self, value):
        self._handle.write_csr64(0xA0 << 2, value)

    @property
    def fin(self):
        # TODO use addresses of config
        return self._handle.read_csr64(0xB0 << 2)

    @fin.setter
    def fin(self, value):
        self._handle.write_csr64(0xB0 << 2, value)
