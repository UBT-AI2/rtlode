import os
import time

from runtime.interface import Solver
from utils import slv
from utils.dict_update import deep_update


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
        deep_update(config, runtime_config)

    # Load bitstream on FPGA
    print('Loading bitstream on fpga...')
    _load_bitstream(gbs_path)

    # Access AFU (get Interface Object)
    print('Aquiring ownership of afu...')
    with Solver(config, 2097152) as solver:
        print('Preparing input...')
        if solver.input_full():
            raise Exception('Input full.')
        else:
            input_id = solver.add_input(
                config['problem']['x'],
                config['problem']['y'],
                config['problem']['h'],
                config['problem']['n']
            )

        print('Starting solver...')
        solver.start()

        while not solver.fin:
            pass

        solver.stop()
        print('Solver finished...')
        res = solver.fetch_output()
        while res['id'] != input_id:
            res = solver.fetch_output()
    return res


def benchmark(slv_path: str, runtime_config=None, amount_data=1000):
    """
    Loads and benchmark a given solver.
    :return:
    """
    runtime_path = os.path.dirname(os.path.realpath(__file__))
    gbs_path = os.path.join(runtime_path, 'solver.gbs')
    config = slv.unpack(slv_path, gbs_path)

    # Patch loaded configs with runtime configuration
    if runtime_config is not None:
        deep_update(config, runtime_config)

    # Load bitstream on FPGA
    print('Loading bitstream on fpga...')
    _load_bitstream(gbs_path)

    # Access AFU (get Interface Object)
    print('Aquiring ownership of afu...')
    with Solver(config, 2097152) as solver:
        print('Preparing input...')
        nbr_inputs = 0
        while nbr_inputs < amount_data and not solver.input_full():
            solver.add_input(
                config['problem']['x'],
                config['problem']['y'],
                config['problem']['h'],
                config['problem']['n']
            )
            nbr_inputs += 1

        print('Starting solver...')
        timing_start = time.time()
        solver.start()

        while not solver.fin:
            pass

        timing_end = time.time()
        solver.stop()
        print('Solver finished...')
    return timing_end - timing_start
