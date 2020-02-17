from opae import fpga


class Solver:

    def __init__(self, config):
        self._config = config

    def __enter__(self):
        tokens = fpga.enumerate(type=fpga.ACCELERATOR, guid=self._config['build_info']['uuid'])
        if tokens is None or len(tokens) < 1:
            raise Exception('No usable afu could be found on fpga.')
        self._fpga = fpga.open(tokens[0], fpga.OPEN_SHARED)
        self._handle = self._fpga.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fpga.__exit__(exc_type, exc_val, exc_tb)
        self._handle = None

    @property
    def h(self):
        # TODO use addresses of config
        return self._handle.read_csr64(0x20)

    @h.setter
    def h(self, value):
        # TODO convert between number formats
        self._handle.write_csr64(0x20, value)
