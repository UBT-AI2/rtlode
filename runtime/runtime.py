import os
import time
from time import sleep

from runtime.interface import Solver
from utils import slv


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


def run(slv_path: str, runtime_config=None, amount_data=1000):
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
    print('Aquiring ownership of afu...')
    with Solver(config, 65536) as solver:
        print('Preparing input...')
        nbr_inputs = 0
        while nbr_inputs < amount_data and not solver.input_full():
            input_id = solver.add_input(
                config['problem']['x'],
                config['problem']['y'],
                config['problem']['h'],
                config['problem']['n']
            )
            print('  Added input: %r' % input_id)
            nbr_inputs += 1

        print('Starting solver...')
        timing_start = time.time()
        solver.start()

        while not solver.fin:
            pass

        timing_end = time.time()
        solver.stop()
        print('Solver finished in: %s' % (timing_end - timing_start))

        for _ in range(nbr_inputs):
            print('Res: %r' % solver.fetch_output())
