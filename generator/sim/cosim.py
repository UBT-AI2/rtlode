import os

from myhdl import Cosimulation, block

from common.config import Config
from generator.cdc_utils import FifoConsumer, FifoProducer
from generator.dispatcher import dispatcher

compile_cmd = 'iverilog -o {output_path} {dut_path} {tb_path}'
cosim_cmd = 'vvp -m {vpi_path} {input_path}'


def get_wrapped_dispatcher(w_config: Config, w_data_in: FifoConsumer, w_data_out: FifoProducer):
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
        return dispatcher(config, data_in, data_out)
    return dispatcher_wrapper(
        w_config,
        w_data_in.clk,
        w_data_in.rst,
        w_data_in.data,
        w_data_in.rd,
        w_data_in.empty,
        w_data_out.data,
        w_data_out.wr,
        w_data_out.full
    )


def dispatcher_cosim(config: Config, data_in: FifoConsumer, data_out: FifoProducer):
    name = 'dispatcher'
    # Step 0: Defines paths
    disp_inst = get_wrapped_dispatcher(config, data_in, data_out)
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'out')
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    bin_path = os.path.join(dir_path, name)
    dut_path = os.path.join(dir_path, name + '.v')
    tb_path = os.path.join(dir_path, 'tb_' + name + '.v')
    vpi_path = os.path.join(dir_path, '..', 'myhdl.vpi')

    convert_testbench = not os.path.isfile(tb_path)

    # Step 1: Convert dispatcher to verilog
    disp_inst.convert(hdl='Verilog', testbench=convert_testbench, name='dispatcher', path=dir_path)

    # Step 2: Compile verilog
    os.system(compile_cmd.format(
        output_path=bin_path,
        dut_path=dut_path,
        tb_path=tb_path
    ))

    # Step 3: Start cosimulation
    return Cosimulation(
        cosim_cmd.format(
            vpi_path=vpi_path,
            input_path=bin_path
        ),
        clk=data_in.clk,
        rst=data_in.rst,
        data_in_data=data_in.data,
        data_in_rd=data_in.rd,
        data_in_empty=data_in.empty,
        data_out_data=data_out.data,
        data_out_wr=data_out.wr,
        data_out_full=data_out.full
    )
