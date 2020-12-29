import json
import os
import shutil
import subprocess
import uuid
from typing import List

import yaml
from myhdl import Signal, ResetSignal, instance, delay, always, always_seq, instances, block, StopSimulation

from framework import data_desc
from generator.ccip import CcipRx, CcipTx
from generator.config import Config
from generator.afu import afu
from generator.cdc_utils import AsyncFifoProducer, AsyncFifoConsumer, async_fifo
from generator.csr import csr_addresses
from framework.packed_struct import BitVector
from generator.dispatcher import dispatcher
from generator.sim.cosim import dispatcher_cosim
from utils import slv, num
from utils.dict_update import deep_update


def _load_config(*files):
    config = {}
    for file in files:
        with open(file, 'r') as stream:
            try:
                deep_update(config, yaml.safe_load(stream))
            except yaml.YAMLError as exc:
                raise exc
    return config


def _build_info():
    return {
        'build_info': {
            'version': subprocess.check_output(["git", "describe", "--tags"]).strip().decode('utf-8'),
            'csr_addresses': csr_addresses,
            'uuid': str(uuid.uuid4())
        }
    }


def _get_build_config(config):
    return {
        "version": 1,
        "afu-image": {
            "power": 0,
            "clock-frequency-high": "auto",
            "clock-frequency-low": "auto",
            "afu-top-interface": {
                "class": "ccip_std_afu",
                "module-ports": [
                    {
                        "class": "cci-p",
                        "params": {
                            "clock": "pClk"
                        }
                    }
                ]
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


def simulate(*config_files, trace=False, buffer_size_bits=4, runtime_config=None, nbr_datasets=10, cosimulate=False):
    current_input_id = 0

    def create_input_data(x_start: float, y_start: List[float], h: int, n: int):
        nonlocal current_input_id
        system_size = len(y_start)

        input_desc = data_desc.get_input_desc(system_size)
        input_data = input_desc.create_write_instance()

        input_data.x_start.next = num.get_default_type().create(x_start)
        for i in range(system_size):
            input_data.y_start[i].next = num.get_default_type().create(y_start[i])
        input_data.h.next = num.get_default_type().create(h)
        input_data.n.next = int(n)

        current_input_id = current_input_id + 1
        input_data.id.next = int(current_input_id)

        input_data.update()
        input_packed = input_data.packed()
        return int(input_packed)

    @block
    def testbench():
        config_dict = _load_config(*config_files)
        if runtime_config is not None:
            deep_update(config_dict, runtime_config)
        config = Config.from_dict(config_dict)

        default_factory = num.NumberType.from_config(config_dict.get('numeric', {}))
        num.set_default_type(default_factory)

        clk = Signal(bool(0))
        reset = ResetSignal(True, True, False)
        usr_clk = Signal(bool(0))
        usr_reset = ResetSignal(True, True, False)

        input_desc_vec = BitVector(len(data_desc.get_input_desc(config.system_size)))
        output_desc_vec = BitVector(len(data_desc.get_output_desc(config.system_size)))

        in_fifo_p = AsyncFifoProducer(clk=clk, rst=reset, data=input_desc_vec.create_instance())
        in_fifo_c = AsyncFifoConsumer(clk=usr_clk, rst=usr_reset, data=input_desc_vec.create_instance())
        in_fifo = async_fifo(in_fifo_p, in_fifo_c, buffer_size_bits=buffer_size_bits)

        out_fifo_p = AsyncFifoProducer(clk=usr_clk, rst=usr_reset, data=output_desc_vec.create_instance())
        out_fifo_c = AsyncFifoConsumer(clk=clk, rst=reset, data=output_desc_vec.create_instance())
        out_fifo = async_fifo(out_fifo_p, out_fifo_c, buffer_size_bits=buffer_size_bits)

        if cosimulate:
            disp_inst = dispatcher_cosim(config, data_in=in_fifo_c, data_out=out_fifo_p)
        else:
            disp_inst = dispatcher(config, data_in=in_fifo_c, data_out=out_fifo_p)

        parsed_output_data = data_desc.get_output_desc(config.system_size).create_read_instance(out_fifo_c.data)

        in_fifo_p.data.next = create_input_data(
            config_dict['problem']['x'],
            config_dict['problem']['y'],
            config_dict['problem']['h'],
            config_dict['problem']['n']
        )
        in_fifo_p.data._update()

        @instance
        def reset_handler():
            yield delay(200)
            reset.next = False
            usr_reset.next = False

        @always(delay(10))
        def clk_driver():
            clk.next = not clk

        @always(delay(43))
        def usr_clk_driver():
            usr_clk.next = not usr_clk

        awaiting_ids = {1: False}
        input_finished = Signal(bool(0))

        @instance
        def p_write():
            yield delay(400)
            in_fifo_p.wr.next = True
            while True:
                yield clk.posedge
                if in_fifo_p.wr and not in_fifo_p.full:
                    if len(awaiting_ids) < nbr_datasets:
                        awaiting_ids[len(awaiting_ids) + 1] = False
                        in_fifo_p.data.next = create_input_data(
                            config_dict['problem']['x'],
                            config_dict['problem']['y'],
                            config_dict['problem']['h'],
                            config_dict['problem']['n']
                        )
                    else:
                        in_fifo_p.wr.next = False
                        input_finished.next = True

        clks = 0
        usr_clks = 0

        @always_seq(out_fifo_p.clk.posedge, reset=None)
        def usr_clk_counter():
            nonlocal usr_clks
            usr_clks = usr_clks + 1

        @always_seq(out_fifo_c.clk.posedge, reset=None)
        def clk_counter():
            nonlocal clks
            clks = clks + 1

        @instance
        def c_read():
            while True:
                for _ in range(20):
                    yield out_fifo_c.clk.posedge
                out_fifo_c.rd.next = True
                yield out_fifo_c.clk.posedge
                if out_fifo_c.rd and not out_fifo_c.empty:
                    y = []
                    for el in parsed_output_data.y:
                        y.append(num.get_default_type().value_of(el))

                    print("Out: %r" % {
                        'x': num.get_default_type().value_of(parsed_output_data.x),
                        'y': y,
                        'id': parsed_output_data.id
                    })

                    pack_id = int(parsed_output_data.id)
                    assert pack_id in awaiting_ids
                    assert not awaiting_ids[pack_id]
                    awaiting_ids[pack_id] = True

                    if input_finished and all(awaiting_ids.values()):
                        print("Finished after %i pclk cycles and %i usr_clk cycles. Received %d packets."
                              % (clks, usr_clks, len(awaiting_ids)))
                        raise StopSimulation()
                out_fifo_c.rd.next = False

        return instances()

    tb = testbench()
    tb.config_sim(trace=trace)
    tb.run_sim()


def convert(config):
    default_factory = num.NumberType.from_config(config.get('numeric', {}))
    num.set_default_type(default_factory)
    cfg = Config.from_dict(config)

    clk = Signal(num.BoolNumberType().create())
    usr_clk = Signal(num.BoolNumberType().create())
    rst = ResetSignal(False, True, False)

    afu_inst = afu(
        cfg,
        clk,
        usr_clk,
        rst,
        BitVector(len(CcipRx)).create_instance(),
        BitVector(len(CcipTx)).create_instance()
    )
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'out')
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    afu_inst.convert(hdl='Verilog', testbench=False, name='solver', path=dir_path)


def build(*config_files, name=None, config=None, cleanup=True):
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
    deep_update(loaded_config, _build_info())
    if config is not None:
        deep_update(loaded_config, config)
    config = loaded_config

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
    if cleanup:
        shutil.rmtree(build_path)
