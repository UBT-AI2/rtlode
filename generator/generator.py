import os
import shutil
import subprocess

import yaml
from myhdl import Simulation, Signal, ResetSignal, delay

from generator import num
from generator.config import Config
from generator.interface import SeqInterface, wrapper_seq
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


def simulate(*config_files):
    config = _load_config(*config_files)
    cfg = Config(config['A'], config['b'], config['c'], config['components'])

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


def convert(*config_files):
    config = _load_config(*config_files)
    cfg = Config(config['A'], config['b'], config['c'], config['components'])

    clk = Signal(num.bool())
    rst = ResetSignal(False, True, False)
    enable = Signal(num.bool())
    finished = Signal(num.bool())

    h = Signal(num.default())
    n = Signal(num.integer())
    x_start = Signal(num.default())
    y_start_addr = Signal(num.integer())
    y_start_val = Signal(num.default())
    x = Signal(num.default())
    y_addr = Signal(num.integer())
    y_val = Signal(num.default())

    interface = SeqInterface(
        FlowControl(clk, rst, enable, finished),
        h,
        n,
        x_start,
        y_start_addr,
        y_start_val,
        x,
        y_addr,
        y_val
    )

    wrapper_inst = wrapper_seq(cfg, interface)
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'out')
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    wrapper_inst.convert(hdl='Verilog', testbench=False, name='solver', path=dir_path)


def build(*config_files, name=None):
    """
    Create solver file for given cofiguration.

    The following steps are performed:
        1. Invokes :func:`convert` to get generated solver in verilog.
        2. Create build directory for synthese with OPAE tools.
        3. Start synthese and fitting.
        4. Create solver file by combining gbs file and solver config.
        5. Clean up build directories.
    :return:
    """
    if name is None:
        name = '_'.join([os.path.basename(file_path).split('.')[0] for file_path in config_files])
        name += slv.FILE_NAME_ENDING

    # 1. Invokes :func:`convert` to get generated solver in verilog.
    convert(*config_files)

    # 2. Create build directory for synthese with OPAE tools.
    build_dir = 'build'
    generator_path = os.path.dirname(os.path.realpath(__file__))
    filelist_path = os.path.join(generator_path, 'static', 'filelist.txt')
    subprocess.run(['afu_synth_setup', '--sources', filelist_path, build_dir], cwd=generator_path).check_returncode()

    # 3. Start synthese and fitting.
    build_path = os.path.join(generator_path, build_dir)
    subprocess.run(['${OPAE_PLATFORM_ROOT}/bin/run.sh'], shell=True, cwd=build_path).check_returncode()

    # 4. Create solver file by combining gbs file and solver config.
    gbs_path = os.path.join(build_path, 'solver.gbs')
    out_path = os.path.join(os.getcwd(), name)
    if not os.path.isfile(gbs_path):
        raise Exception('solver.gbs output file from synthesis could not be found.')
    config = _load_config(*config_files)
    slv.pack(gbs_path, config, out_path)

    # 5. Clean up build directories.
    shutil.rmtree(build_path)
