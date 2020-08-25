from myhdl import block, instances, SignalType, always, Signal, always_comb, always_seq

from framework import data_desc
from framework.packed_struct import StructDescription, StructDescriptionMetaclass, List, BitVector
from generator.fifo import FifoConsumer, FifoProducer, fifo
from generator.pipeline import PipeInput, PipeOutput, Pipe, PipeConstant
from generator.vector_utils import vec_mul
from generator.utils import assign, assign_3, assign_2
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
    solver_output_reg = solver_output_desc.create_write_instance()
    solver_output_reg_filled = Signal(bool(0))

    if '_bit_padding' in solver_output_desc.get_fields():
        @always_seq(clk.posedge, reset=None)
        def drive_output_bit_padding():
            solver_output._bit_padding.next = 0

    class PipeData(StructDescription, metaclass=StructDescriptionMetaclass):
        id = BitVector(num.INTEGER_SIZE)
        h = BitVector(num.TOTAL_SIZE)
        n = BitVector(num.TOTAL_SIZE)
        cn = BitVector(num.TOTAL_SIZE)
        x = BitVector(num.TOTAL_SIZE)
        y = List(config.system_size, BitVector(num.TOTAL_SIZE))

    pipe_input_valid = Signal(bool(0))
    pipe_output_busy = Signal(bool(0))

    pipe_input_id = Signal(num.integer())
    pipe_input_h = Signal(num.default())
    pipe_input_n = Signal(num.integer())
    pipe_input_cn = Signal(num.integer())
    pipe_input_x = Signal(num.default())
    pipe_input_y = [Signal(num.default()) for _ in range(config.system_size)]

    cycle_p = FifoProducer(BitVector(len(PipeData)).create_instance())
    cycle_c = FifoConsumer(BitVector(len(PipeData)).create_instance())
    cycle_fifo = fifo(clk, rst, cycle_p, cycle_c, buffer_size_bits=2)
    cycle_input = PipeData.create_write_instance()
    cycle_input_packed = cycle_input.packed()
    cycle_input_reg = PipeData.create_write_instance()
    cycle_input_reg_filled = Signal(bool(0))
    cycle_output = PipeData.create_read_instance(cycle_c.data)

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

    y_n = [
        pipe_data_in.y[i] + pipe_data_in.h * vec_mul(
            [PipeConstant.from_float(el) for el in config.b],
            [el[i] for el in v]
        ) for i in range(config.system_size)
    ]

    pipe_data_out = PipeOutput(pipe_output_busy,
                               id=pipe_data_in.id,
                               h=pipe_data_in.h,
                               n=pipe_data_in.n,
                               cn=pipe_data_in.cn + PipeConstant(1),
                               x=pipe_data_in.x + pipe_data_in.h,
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
            cycle_p.wr.next = False
            solver_input_reg_filled.next = False
            solver_output_reg_filled.next = False
            cycle_input_reg_filled.next = False
        else:
            if not pipe_data_in.pipe_busy:
                if cycle_c.rd and not cycle_c.empty:
                    pipe_input_id.next = cycle_output.id
                    pipe_input_h.next = cycle_output.h
                    pipe_input_n.next = cycle_output.n
                    pipe_input_cn.next = cycle_output.cn
                    pipe_input_x.next = cycle_output.x
                    pipe_input_valid.next = True
                    if data_in.rd and not data_in.empty:
                        # Save into register
                        solver_input_reg.id.next = solver_input.id
                        solver_input_reg.h.next = solver_input.h
                        solver_input_reg.n.next = solver_input.n
                        solver_input_reg.x_start.next = solver_input.x_start

                        solver_input_reg_filled.next = True
                        data_in.rd.next = False
                elif data_in.rd and not data_in.empty:
                    pipe_input_id.next = solver_input.id
                    pipe_input_h.next = solver_input.h
                    pipe_input_n.next = solver_input.n
                    pipe_input_cn.next = 0
                    pipe_input_x.next = solver_input.x_start
                    pipe_input_valid.next = True
                    data_in.rd.next = True
                elif solver_input_reg_filled:
                    pipe_input_id.next = solver_input_reg.id
                    pipe_input_h.next = solver_input_reg.h
                    pipe_input_n.next = solver_input_reg.n
                    pipe_input_cn.next = 0
                    pipe_input_x.next = solver_input_reg.x_start
                    pipe_input_valid.next = True

                    solver_input_reg_filled.next = False
                    data_in.rd.next = True
                else:
                    pipe_input_valid.next = False
            else:
                if data_in.rd and not data_in.empty:
                    # Save into register
                    solver_input_reg.id.next = solver_input.id
                    solver_input_reg.h.next = solver_input.h
                    solver_input_reg.n.next = solver_input.n
                    solver_input_reg.x_start.next = solver_input.x_start

                    solver_input_reg_filled.next = True
                    data_in.rd.next = False

            # Output
            if not data_out.full:
                if solver_output_reg_filled:
                    # From register
                    solver_output.id.next = solver_output_reg.id
                    solver_output.x.next = solver_output_reg.x

                    solver_output_reg_filled.next = False
                    data_out.wr.next = True
                elif not pipe_output_busy and pipe_data_out.pipe_valid and pipe_data_out.cn >= pipe_data_out.n:
                    # Directly pass
                    solver_output.id.next = pipe_data_out.id
                    solver_output.x.next = pipe_data_out.x

                    data_out.wr.next = True
                else:
                    data_out.wr.next = False
            else:
                if not pipe_output_busy and pipe_data_out.pipe_valid and pipe_data_out.cn >= pipe_data_out.n:
                    # Save to reg
                    solver_output_reg.id.next = pipe_data_out.id
                    solver_output_reg.x.next = pipe_data_out.x

                    solver_output_reg_filled.next = True

            if not cycle_p.full:
                if cycle_input_reg_filled:
                    # From register
                    cycle_input.id.next = cycle_input_reg.id
                    cycle_input.h.next = cycle_input_reg.h
                    cycle_input.n.next = cycle_input_reg.n
                    cycle_input.cn.next = cycle_input_reg.cn
                    cycle_input.x.next = cycle_input_reg.x

                    cycle_input_reg_filled.next = False
                    cycle_p.wr.next = True
                elif not pipe_output_busy and pipe_data_out.pipe_valid\
                        and pipe_data_out.cn < pipe_data_out.n:
                    # Directly pass
                    cycle_input.id.next = pipe_data_out.id
                    cycle_input.h.next = pipe_data_out.h
                    cycle_input.n.next = pipe_data_out.n
                    cycle_input.cn.next = pipe_data_out.cn
                    cycle_input.x.next = pipe_data_out.x

                    cycle_p.wr.next = True
                else:
                    cycle_p.wr.next = False
            else:
                if not pipe_output_busy and pipe_data_out.pipe_valid and pipe_data_out.cn < pipe_data_out.n:
                    # Save to reg
                    cycle_input_reg.id.next = pipe_data_out.id
                    cycle_input_reg.h.next = pipe_data_out.h
                    cycle_input_reg.n.next = pipe_data_out.n
                    cycle_input_reg.cn.next = pipe_data_out.cn
                    cycle_input_reg.x.next = pipe_data_out.x

                    cycle_input_reg_filled.next = True

    do_cycle_output_to_pipe_input = Signal(bool(0))
    do_solver_input_to_solver_reg = Signal(bool(0))
    do_solver_input_to_pipe_input = Signal(bool(0))
    do_solver_reg_to_pipe_input = Signal(bool(0))

    @always_comb
    def input_state_driver():
        do_cycle_output_to_pipe_input.next = False
        do_solver_input_to_solver_reg.next = False
        do_solver_input_to_pipe_input.next = False
        do_solver_reg_to_pipe_input.next = False
        if not pipe_data_in.pipe_busy:
            if cycle_c.rd and not cycle_c.empty:
                do_cycle_output_to_pipe_input.next = True
                if data_in.rd and not data_in.empty:
                    # Save into register
                    do_solver_input_to_solver_reg.next = True
            elif data_in.rd and not data_in.empty:
                do_solver_input_to_pipe_input.next = True
            elif solver_input_reg_filled:
                do_solver_reg_to_pipe_input.next = True
        else:
            if data_in.rd and not data_in.empty:
                # Save into register
                do_solver_input_to_solver_reg.next = True

    do_solver_output_reg_to_solver_output = Signal(bool(0))
    do_pipe_output_reg_to_solver_output = Signal(bool(0))
    do_pipe_output_to_solver_output_reg = Signal(bool(0))
    do_cycle_input_reg_to_cycle_input = Signal(bool(0))
    do_pipe_output_to_cycle_input = Signal(bool(0))
    do_pipe_output_to_cycle_input_reg = Signal(bool(0))

    @always_comb
    def output_state_driver():
        do_solver_output_reg_to_solver_output.next = False
        do_pipe_output_reg_to_solver_output.next = False
        do_pipe_output_to_solver_output_reg.next = False
        if not data_out.full:
            if solver_output_reg_filled:
                # From register
                do_solver_output_reg_to_solver_output.next = True
            elif not pipe_output_busy and pipe_data_out.pipe_valid and pipe_data_out.cn >= pipe_data_out.n:
                # Directly pass
                do_pipe_output_reg_to_solver_output.next = True
        else:
            if not pipe_output_busy and pipe_data_out.pipe_valid and pipe_data_out.cn >= pipe_data_out.n:
                # Save to reg
                do_pipe_output_to_solver_output_reg.next = True

        do_cycle_input_reg_to_cycle_input.next = False
        do_pipe_output_to_cycle_input.next = False
        do_pipe_output_to_cycle_input_reg.next = False

        if not cycle_p.full:
            if cycle_input_reg_filled:
                # From register
                do_cycle_input_reg_to_cycle_input.next = True
            elif not pipe_output_busy and pipe_data_out.pipe_valid \
                    and pipe_data_out.cn < pipe_data_out.n:
                # Directly pass
                do_pipe_output_to_cycle_input.next = True
        else:
            if not pipe_output_busy and pipe_data_out.pipe_valid and pipe_data_out.cn < pipe_data_out.n:
                # Save to reg
                do_pipe_output_to_cycle_input_reg.next = True

    @always_comb
    def pipe_output_busy_driver():
        pipe_output_busy.next = solver_output_reg_filled or cycle_input_reg_filled

    @always_comb
    def cycle_rd_driver():
        cycle_c.rd.next = not pipe_data_in.pipe_busy

    @always_comb
    def cycle_input_driver():
        cycle_p.data.next = cycle_input_packed

    @always_comb
    def assign_solver_output():
        data_out.data.next = solver_output_packed

    y_data_in_store = [
        assign(clk, do_solver_input_to_solver_reg, solver_input.y_start[i], solver_input_reg.y_start[i])
        for i in range(config.system_size)
    ]

    y_data_in = [
        assign_3(clk,
                 do_solver_input_to_pipe_input, solver_input.y_start[i],
                 do_cycle_output_to_pipe_input, cycle_output.y[i],
                 do_solver_reg_to_pipe_input, solver_input_reg.y_start[i],
                 pipe_input_y[i])
        for i in range(config.system_size)
    ]

    y_data_out = [
        assign_2(clk,
                 do_solver_output_reg_to_solver_output, solver_output_reg.y[i],
                 do_pipe_output_reg_to_solver_output, pipe_data_out.y[i],
                 solver_output.y[i])
        for i in range(config.system_size)
    ]

    y_data_out_store = [
        assign(clk, do_pipe_output_to_solver_output_reg, pipe_data_out.y[i], solver_output_reg.y[i])
        for i in range(config.system_size)
    ]

    y_cycle_in = [
        assign_2(clk,
                 do_cycle_input_reg_to_cycle_input, cycle_input_reg.y[i],
                 do_pipe_output_to_cycle_input, pipe_data_out.y[i],
                 cycle_input.y[i])
        for i in range(config.system_size)
    ]

    y_cycle_store = [
        assign(clk, do_pipe_output_to_cycle_input_reg, pipe_data_out.y[i], cycle_input_reg.y[i])
        for i in range(config.system_size)
    ]

    return instances()
