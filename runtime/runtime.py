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
    print('Aquiring ownership of afu...')
    with Solver(config, 4096) as solver:
        print('Starting solver...')

        timing_start = time.time()

        nbr_datasets = 10
        nbr_results = 0
        nbr_inputs = 0
        while nbr_results != nbr_datasets:
            if not solver.input_full() and nbr_inputs < nbr_datasets:
                nbr_inputs = nbr_inputs + 1
                data_id = solver.add_input(0, config['y'], config['h'], config['n'])
                print('Added new input dataset: %s' % data_id)

            output = solver.fetch_output()
            if output is not None:
                nbr_results = nbr_results + 1
                print('Fetched output dataset: %s' % output['id'])
                for i, val in enumerate(output['y']):
                    print('y[%s] = %s' % (i, val))

            sleep(0.1)

        timing_end = time.time()
        print('Solver finished in: %s' % (timing_end - timing_start))
