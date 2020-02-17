import os

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
    _load_bitstream(gbs_path)

    # Access AFU (get Interface Object)
    with Solver(config) as solver:
        # TODO implement
        solver.h = 20

        # Set h, n, x_start, y_start

        # Enable solver

        # Wait until finished

        # Read x and y

    pass