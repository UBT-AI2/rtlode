import os
import time
from time import sleep

from runtime.interface import Solver
from utils import slv, num


def _load_bitstream(gbs_path: str):
    """
    Loads a bitstream given by file to a connected FPGA card.
    """
    from opae import fpga

    tokens = fpga.enumerate(type=fpga.DEVICE)
    if tokens is None or len(tokens) < 1:
        raise Exception('Could not find any compatible FPGA.')
    with open(gbs_path, 'rb') as fd, fpga.open(tokens[0]) as device:
        device.reconfigure(0, fd)


def run(slv_path: str, runtime_config=None):
    """
    Loads and run a given solver.

    :return:
    """
    runtime_path = os.path.dirname(os.path.realpath(__file__))
    gbs_path = os.path.join(runtime_path, 'solver.gbs')
    config = slv.unpack(slv_path, gbs_path)

    # Patch loaded configs with runtime configuration
    if runtime_config is not None:
        config.update(runtime_config)

    # Load bitstream on FPGA
    print('Loading bitstream on fpga...')
    _load_bitstream(gbs_path)

    # Access AFU (get Interface Object)
    print('Aquire ownership of afu...')
    with Solver(config, 4096) as solver:
        print('Configure solver...')
        solver.h = config['h']
        solver.n = config['n']
        solver.x_start = 0
        # for i, y in enumerate(config['y']):
        #     solver.y_start_addr = i
        #     solver.y_start_val = y
        for i, y in enumerate(config['y']):
            val_bytes = int(num.from_float(y)).to_bytes(8, byteorder='little', signed=True)
            for bi, b in enumerate(val_bytes):
                solver.y_start[i*8+bi] = b

        print('Start solver...')
        timing_start = time.time()
        solver.enb = 1
        while solver.fin != 1:
            sleep(0.1)
        timing_end = time.time()
        print('Solver finished in: %s' % (timing_end - timing_start))
        print('x = %s' % solver.x)
        # for i, y in enumerate(config['y']):
        #     solver.y_addr = i
        #     print('y[%s] = %s' % (i, solver.y_val))
        for i, _ in enumerate(config['y']):
            val = int.from_bytes(solver.y[i*8:(i+1)*8], byteorder='little', signed=True)
            print('y[%s]: %s' % (i, num.to_float(val)))
