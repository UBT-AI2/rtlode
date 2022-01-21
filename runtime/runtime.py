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


def run(slv_path: str, runtime_config=None, amount_data=None):
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
    info_msg = ''
    if config['build_info'].get('datetime') is not None:
        info_msg += f" at {config['build_info']['datetime']}"
    if config['build_info'].get('version') is not None:
        info_msg += f" with version {config['build_info']['version']}"
    if len(info_msg) > 0:
        print(f"Solver was build{info_msg}...")

    # Load bitstream on FPGA
    print('Loading bitstream on fpga...')
    _load_bitstream(gbs_path)

    # Access AFU (get Interface Object)
    print('Aquiring ownership of afu...')
    with Solver(config, 2097152) as solver:
        print('Preparing input...')
        nbr_inputs = 0
        awaiting_ids = {}
        while nbr_inputs < amount_data and not solver.input_full():
            package_id = solver.add_input(
                config['problem']['x'],
                config['problem']['y'],
                config['problem']['h'],
                config['problem']['n']
            )
            nbr_inputs += 1
            awaiting_ids[package_id] = False

        print('Starting solver...')
        solver.start()

        while not solver.fin:
            pass

        solver.stop()
        print('Solver finished...')

        results = []
        while not all(awaiting_ids.values()):
            package_res = solver.fetch_output()
            if package_res is None:
                raise Exception('Did not receive all outputs.')
            if package_res['id'] in awaiting_ids:
                if awaiting_ids[package_res['id']]:
                    raise Exception('Already got results for this id.')
                awaiting_ids[package_res['id']] = True
                results.append(package_res)
    return results


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
    info_msg = ''
    if config['build_info'].get('datetime') is not None:
        info_msg += f" at {config['build_info']['datetime']}"
    if config['build_info'].get('version') is not None:
        info_msg += f" with version {config['build_info']['version']}"
    if len(info_msg) > 0:
        print(f"Solver was build{info_msg}...")

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
