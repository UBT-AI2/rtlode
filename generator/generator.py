import json
import os
import shutil
import subprocess
import uuid

import yaml
from myhdl import Simulation, Signal, ResetSignal, delay

from generator import num
from generator.ccip import CcipRx, CcipTx
from generator.config import Config
from generator.afu import afu, csr_addresses
from generator.packed_struct import BitVector
from generator.runge_kutta import rk_solver, RKInterface
from generator.flow import FlowControl
from utils import slv


def _load_config(*files):
    config = {}
    for file in files:
        with open(file, 'r') as stream:
            try:
                config.update(yaml.safe_load(stream))
            except yaml.YAMLError as exc:
                raise exc
    return config


def _build_info():
    return {
        'build_info': {
            'version': subprocess.check_output(["git", "describe", "--tags"]).strip(),
            'csr_addresses': csr_addresses,
            'uuid': str(uuid.uuid4())
        }
    }


def _get_build_config(config):
    return {
       "version": 1,
       "afu-image": {
          "power": 0,
          "afu-top-interface":
             {
                "class": "ccip_std_afu"
             },
          "accelerator-clusters":
             [
                {
                   "name": "solver",
                   "total-contexts": 1,
                   "accelerator-type-uuid": config['build_info']['uuid']
                }
             ]
       }
    }


def _create_build_config(config):
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'out', 'solver.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(_get_build_config(config), f, ensure_ascii=False, indent=2)


def simulate(*config_files):
    config = _load_config(*config_files)
    cfg = Config(
        config['method']['A'],
        config['method']['b'],
        config['method']['c'],
        config['components']
    )

    clk = Signal(bool(0))
    rst = ResetSignal(False, True, False)
    enable = Signal(bool(0))
    finished = Signal(bool(0))

    h = Signal(num.from_float(config['h']))
    n = Signal(num.integer(config['n']))
    x_start = Signal(num.from_float(config['x']))
    y_start = [Signal(num.from_float(config['y'][i])) for i in range(cfg.system_size)]
    x = Signal(num.default())
    y = [Signal(num.default()) for _ in range(cfg.system_size)]

    interface = RKInterface(FlowControl(clk, rst, enable, finished), h, n, x_start, y_start, x, y)

    def test():
        rst.next = True
        yield delay(10)
        clk.next = not clk
        yield delay(10)
        clk.next = not clk
        rst.next = False
        yield delay(10)
        clk.next = not clk
        yield delay(10)
        clk.next = not clk
        yield delay(10)
        clk.next = not clk
        yield delay(10)
        clk.next = not clk
        enable.next = 1

        clks = 0
        while finished != 1:
            yield delay(10)
            clk.next = not clk
            clks += 1
            yield delay(10)
            clk.next = not clk

        print("Finished after %i clock cycles." % clks)

    dut = rk_solver(cfg, interface)
    testdriver = test()
    sim_inst = Simulation(dut, testdriver)
    sim_inst.run(quiet=1)


def convert(config):
    cfg = Config(
        config['method']['A'],
        config['method']['b'],
        config['method']['c'],
        config['components'],
        uuid=config['build_info']['uuid']
    )

    clk = Signal(num.bool())
    rst = ResetSignal(False, True, False)

    wrapper_inst = afu(
        cfg,
        clk,
        rst,
        BitVector(len(CcipRx)).create_instance(),
        BitVector(len(CcipTx)).create_instance()
    )
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'out')
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    wrapper_inst.convert(hdl='Verilog', testbench=False, name='solver', path=dir_path)


def build(*config_files, name=None, config=None):
    """
    Create solver file for given cofiguration.

    The following steps are performed:
        1. Load and enrich config
        2. Invokes :func:`convert` to get generated solver in verilog.
        3. Create build directory for synthese with OPAE tools.
        4. Start synthese and fitting.
        5. Create solver file by combining gbs file and solver config.
        6. Clean up build directories.
    :return:
    """
    if name is None:
        name = '_'.join([os.path.basename(file_path).split('.')[0] for file_path in config_files])
        name += slv.FILE_NAME_ENDING

    # 1. Load and enrich config
    loaded_config = _load_config(*config_files)
    if config is not None:
        config.update(loaded_config)
    else:
        config = loaded_config
    config.update(_build_info())

    # 2. Invokes :func:`convert` to get generated solver in verilog.
    convert(config)

    # 3. Create build directory for synthese with OPAE tools.
    _create_build_config(config)
    build_dir = 'build'
    generator_path = os.path.dirname(os.path.realpath(__file__))
    filelist_path = os.path.join(generator_path, 'static', 'filelist.txt')
    subprocess.run(['afu_synth_setup', '--sources', filelist_path, build_dir], cwd=generator_path).check_returncode()

    # 4. Start synthese and fitting.
    build_path = os.path.join(generator_path, build_dir)
    subprocess.run(['${OPAE_PLATFORM_ROOT}/bin/run.sh'], shell=True, cwd=build_path).check_returncode()

    # 5. Create solver file by combining gbs file and solver config.
    gbs_path = os.path.join(build_path, 'solver.gbs')
    out_path = os.path.join(os.getcwd(), name)
    if not os.path.isfile(gbs_path):
        raise Exception('solver.gbs output file from synthesis could not be found.')
    slv.pack(gbs_path, config, out_path)

    # 6. Clean up build directories.
    shutil.rmtree(build_path)
