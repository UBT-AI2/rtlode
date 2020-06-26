from myhdl import block, instances, SignalType, always, Signal, always_comb, always_seq

from common import data_desc
from generator.fifo import FifoConsumer, FifoProducer
from generator.pipeline import PipeInput, PipeOutput, Pipe
from generator.pipeline_elements import add, vec_mul, mul
from generator.utils import assign, assign_3
from utils import num
from generator.config import Config
from generator.rk_stage import stage


@block
def solver(
        config: Config,
        clk: SignalType,
        rst: SignalType,
        data_in: FifoConsumer,
        data_out: FifoProducer
):
    solver_input_desc = data_desc.get_input_desc(config.system_size)
    solver_input = solver_input_desc.create_read_instance(data_in.data)
    solver_input_reg_filled = Signal(bool(0))
    solver_input_reg = solver_input_desc.create_write_instance()

    solver_output_desc = data_desc.get_output_desc(config.system_size)
    solver_output = solver_output_desc.create_write_instance()
    solver_output_packed = solver_output.packed()

    if '_bit_padding' in solver_output_desc.get_fields():
        @always_seq(clk.posedge, reset=None)
        def drive_output_bit_padding():
            solver_output._bit_padding.next = 0

    pipe_input_valid = Signal(bool(0))
    pipe_output_busy = Signal(bool(0))

    pipe_input_id = Signal(num.integer())
    pipe_input_h = Signal(num.default())
    pipe_input_n = Signal(num.integer())
    pipe_input_cn = Signal(num.integer())
    pipe_input_x = Signal(num.default())
    pipe_input_y = [Signal(num.default()) for _ in range(config.system_size)]

    pipe_data_in = PipeInput(pipe_input_valid,
                             id=pipe_input_id,
                             h=pipe_input_h,
                             n=pipe_input_n,
                             cn=pipe_input_cn,
                             x=pipe_input_x,
                             y=pipe_input_y)
    v = []
    for si in range(config.stages):
        v.append(
            stage(config.get_stage_config(si), pipe_data_in.h, pipe_data_in.x, pipe_data_in.y, v)
        )

    x_n = add(pipe_data_in.x, pipe_data_in.h)
    y_n = []
    for i in range(config.system_size):
        vec = vec_mul(
            [num.int_from_float(el) for el in config.b],
            [el[i] for el in v]
        )
        mul_res = mul(pipe_data_in.h, vec)
        y_n.append(add(pipe_data_in.y[i], mul_res))

    cn_n = add(pipe_data_in.cn, 1)

    pipe_data_out = PipeOutput(pipe_output_busy,
                               id=pipe_data_in.id,
                               h=pipe_data_in.h,
                               n=pipe_data_in.n,
                               cn=cn_n,
                               x=x_n,
                               y=y_n)
    pipe = Pipe(pipe_data_in, pipe_data_out)
    print(pipe.get_stats())
    pipe_inst = pipe.create(clk, rst)

    @always(clk.posedge)
    def state_machine():
        if rst:
            pipe_input_valid.next = False
            data_in.rd.next = True
            data_out.wr.next = False
            solver_input_reg_filled.next = False
        else:
            # Print debug informations
            if __debug__:
                if pipe_data_out.pipe_valid:
                    for i in range(config.system_size):
                        print('Id: %d\t[%d] %f = %f' % (
                            pipe_data_out.id,
                            i,
                            num.to_float(pipe_data_out.x),
                            num.to_float(pipe_data_out.y[i])
                        ))

            if pipe_data_out.pipe_valid and pipe_data_out.cn < pipe_data_out.n:
                pipe_input_id.next = pipe_data_out.id
                pipe_input_h.next = pipe_data_out.h
                pipe_input_n.next = pipe_data_out.n
                pipe_input_cn.next = pipe_data_out.cn
                pipe_input_x.next = pipe_data_out.x
                pipe_input_valid.next = True

                if data_in.rd and not data_in.empty:
                    # Save into register
                    solver_input_reg.id.next = solver_input.id
                    solver_input_reg.h.next = solver_input.h
                    solver_input_reg.n.next = solver_input.n
                    solver_input_reg.x_start.next = solver_input.x_start

                    solver_input_reg_filled.next = True
                    data_in.rd.next = False
                    if __debug__:
                        print("Saved into reg: %d" % solver_input.id)
            elif data_in.rd and not data_in.empty:
                pipe_input_id.next = solver_input.id
                pipe_input_h.next = solver_input.h
                pipe_input_n.next = solver_input.n
                pipe_input_cn.next = 0
                pipe_input_x.next = solver_input.x_start
                pipe_input_valid.next = True
                data_in.rd.next = True
                if __debug__:
                    print("Got input: %d" % solver_input.id)
            elif solver_input_reg_filled:
                pipe_input_id.next = solver_input_reg.id
                pipe_input_h.next = solver_input_reg.h
                pipe_input_n.next = solver_input_reg.n
                pipe_input_cn.next = 0
                pipe_input_x.next = solver_input_reg.x_start
                pipe_input_valid.next = True

                solver_input_reg_filled.next = False
                data_in.rd.next = True
                if __debug__:
                    print("Loaded from reg: %d" % solver_input_reg.id)
            else:
                pipe_input_valid.next = False

            if pipe_data_out.pipe_valid and pipe_data_out.cn >= pipe_data_out.n:
                # Solver data finished, send
                solver_output.id.next = pipe_data_out.id
                solver_output.x.next = pipe_data_out.x
                if __debug__:
                    print("Added output: %d" % pipe_data_out.id)
                data_out.wr.next = True
            else:
                data_out.wr.next = False

    do_data_store = Signal(bool(0))
    do_data_in = Signal(bool(0))
    do_data_cycle = Signal(bool(0))
    do_data_load = Signal(bool(0))
    do_data_out = Signal(bool(0))

    @always_comb
    def do_data_store_driver():
        do_data_store.next = do_data_cycle and (data_in.rd and not data_in.empty)

    @always_comb
    def do_data_in_driver():
        do_data_in.next = not do_data_cycle and (data_in.rd and not data_in.empty)

    @always_comb
    def do_data_cycle_driver():
        do_data_cycle.next = pipe_data_out.pipe_valid and pipe_data_out.cn < pipe_data_out.n

    @always_comb
    def do_data_load_driver():
        do_data_load.next = not do_data_cycle and not do_data_in and solver_input_reg_filled

    @always_comb
    def do_data_out_driver():
        do_data_out.next = pipe_data_out.pipe_valid and pipe_data_out.cn >= pipe_data_out.n

    y_data_store = [
        assign(clk, do_data_store, solver_input.y_start[i], solver_input_reg.y_start[i])
        for i in range(config.system_size)
    ]

    y_data_in = [
        assign_3(clk,
                 do_data_in, solver_input.y_start[i],
                 do_data_cycle, pipe_data_out.y[i],
                 do_data_load, solver_input_reg.y_start[i],
                 pipe_input_y[i])
        for i in range(config.system_size)
    ]

    y_data_out = [
        assign(clk, do_data_out, pipe_data_out.y[i], solver_output.y[i])
        for i in range(config.system_size)
    ]

    @always_comb
    def pipe_busy_driver():
        pipe_output_busy.next = data_out.full

    @always_comb
    def assign_solver_output():
        data_out.data.next = solver_output_packed

    return instances()
