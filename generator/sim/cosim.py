import os
import subprocess

from myhdl import Cosimulation, block, SignalType

from generator.config import Config
from generator.cdc_utils import AsyncFifoConsumer, AsyncFifoProducer
from generator.fifo import ByteFifoProducer, ByteFifoConsumer

compile_cmd = 'iverilog -o {output_path} {dut_path} {tb_path}'
cosim_cmd = 'vvp -m {vpi_path} {input_path}'


def dispatcher_cosim(config: Config, data_in: AsyncFifoConsumer, data_out: AsyncFifoProducer):
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
        data_in = AsyncFifoConsumer(clk=clk, rst=rst, data=data_in_data, rd=data_in_rd, empty=data_in_empty)
        data_out = AsyncFifoProducer(clk=clk, rst=rst, data=data_out_data, wr=data_out_wr, full=data_out_full)
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


def byte_fifo_cosim(clk: SignalType, rst: SignalType, p: ByteFifoProducer, c: ByteFifoConsumer, buffer_size=None):
    # noinspection PyShadowingNames
    @block
    def byte_fifo_wrapper(clk,
                          rst,
                          p_data,
                          p_wr,
                          p_full,
                          p_data_size,
                          c_data,
                          c_rd,
                          c_empty,
                          c_data_size,
                          buffer_size=None):
        p = ByteFifoProducer(p_data, p_wr, p_full, p_data_size)
        c = ByteFifoConsumer(c_data, c_rd, c_empty, c_data_size)
        from generator.fifo import byte_fifo
        return byte_fifo(clk, rst, p, c, buffer_size)

    dut = byte_fifo_wrapper(
            clk,
            rst,
            p.data,
            p.wr,
            p.full,
            p.data_size,
            c.data,
            c.rd,
            c.empty,
            c.data_size,
            buffer_size
        )

    return cosim(
        dut,
        'byte_fifo_wrapper',
        clk=clk,
        rst=rst,
        p_data=p.data,
        p_wr=p.wr,
        p_full=p.full,
        p_data_size=p.data_size,
        c_data=c.data,
        c_rd=c.rd,
        c_empty=c.empty,
        c_data_size=c.data_size
    )


def afu_cosim(config: Config, clk: SignalType, usr_clk: SignalType, reset: SignalType, cp2af_port: SignalType,
              af2cp_port: SignalType):
    # noinspection PyShadowingNames
    from generator.afu import afu
    dut = afu(config, clk, usr_clk, reset, cp2af_port, af2cp_port)

    return cosim(
        dut,
        'afu',
        clk=clk,
        usr_clk=usr_clk,
        reset=reset,
        cp2af_port=cp2af_port,
        af2cp_port=af2cp_port
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
