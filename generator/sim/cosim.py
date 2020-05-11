import os
import subprocess

from myhdl import Cosimulation, block, SignalType

from common.config import Config
from generator.cdc_utils import FifoConsumer, FifoProducer

compile_cmd = 'iverilog -o {output_path} {dut_path} {tb_path}'
cosim_cmd = 'vvp -m {vpi_path} {input_path}'


def dispatcher_cosim(config: Config, data_in: FifoConsumer, data_out: FifoProducer):
    # noinspection PyShadowingNames
    @block
    def dispatcher_wrapper(config: Config,
                           clk,
                           rst,
                           data_in_data,
                           data_in_rd,
                           data_in_empty,
                           data_out_data,
                           data_out_wr,
                           data_out_full):
        data_in = FifoConsumer(clk, rst, data_in_data, data_in_rd, data_in_empty)
        data_out = FifoProducer(clk, rst, data_out_data, data_out_wr, data_out_full)
        from generator.dispatcher import dispatcher
        return dispatcher(config, data_in, data_out)

    dut = dispatcher_wrapper(
            config,
            data_in.clk,
            data_in.rst,
            data_in.data,
            data_in.rd,
            data_in.empty,
            data_out.data,
            data_out.wr,
            data_out.full
        )

    return cosim(
        dut,
        'dispatcher',
        clk=data_in.clk,
        rst=data_in.rst,
        data_in_data=data_in.data,
        data_in_rd=data_in.rd,
        data_in_empty=data_in.empty,
        data_out_data=data_out.data,
        data_out_wr=data_out.wr,
        data_out_full=data_out.full
    )


def data_chunk_parser_cosim(
        config: Config,
        data_out: FifoProducer,
        chunk_in: FifoProducer,
        input_ack_id: SignalType,
        drop: SignalType,
        drop_bytes: SignalType):
    # noinspection PyShadowingNames
    @block
    def data_chunk_parser_wrapper(config: Config, clk, rst, data_out_data, data_out_wr, data_out_full,
                                  chunk_in_data, chunk_in_wr, chunk_in_full, input_ack_id, drop, drop_bytes):
        data_out = FifoProducer(clk, rst, data_out_data, data_out_wr, data_out_full)
        chunk_in = FifoProducer(clk, rst, chunk_in_data, chunk_in_wr, chunk_in_full)
        from generator.hram import data_chunk_parser
        return data_chunk_parser(config, data_out, chunk_in, input_ack_id, drop, drop_bytes)

    dut = data_chunk_parser_wrapper(
            config,
            data_out.clk,
            data_out.rst,
            data_out.data,
            data_out.wr,
            data_out.full,
            chunk_in.data,
            chunk_in.wr,
            chunk_in.full,
            input_ack_id,
            drop,
            drop_bytes
        )

    return cosim(
        dut,
        'data_chunk_parser',
        clk=data_out.clk,
        rst=data_out.rst,
        data_out_data=data_out.data,
        data_out_wr=data_out.wr,
        data_out_full=data_out.full,
        chunk_in_data=chunk_in.data,
        chunk_in_wr=chunk_in.wr,
        chunk_in_full=chunk_in.full,
        input_ack_id=input_ack_id,
        drop=drop,
        drop_bytes=drop_bytes
    )


def cosim(dut, name, **signals):
    """
    Initialize cosimulation (icarus verilog) for an given dut.
    :param dut: myhdl block instace of dut
    :param name: name of dut
    :param signals: all signals connecting the dut
    :return: cosimulation object which can be used as replacement of dut in sim
    """
    # Step 0: Defines paths
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'out')
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    bin_path = os.path.join(dir_path, name)
    dut_path = os.path.join(dir_path, name + '.v')
    tb_path = os.path.join(dir_path, 'tb_' + name + '.v')
    vpi_path = os.path.join(dir_path, '..', 'myhdl.vpi')

    convert_testbench = not os.path.isfile(tb_path)

    # Step 1: Convert dut to verilog
    dut.convert(hdl='Verilog', testbench=convert_testbench, name=name, path=dir_path)

    # Step 2: Compile verilog
    subprocess.call(compile_cmd.format(
        output_path=bin_path,
        dut_path=dut_path,
        tb_path=tb_path
    ), shell=True)

    # Step 3: Start cosimulation
    return Cosimulation(
        cosim_cmd.format(
            vpi_path=vpi_path,
            input_path=bin_path
        ),
        **signals
    )
