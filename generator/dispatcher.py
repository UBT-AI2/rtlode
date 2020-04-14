from myhdl import block, always_seq, enum, Signal, instances, always_comb

from generator.cdc_utils import FifoConsumer, FifoProducer
from generator.flow import FlowControl
from common.data_desc import get_input_desc, get_output_desc
from generator.runge_kutta import SolverInterface, rk_solver
from utils import num

t_state = enum('IDLE', 'BUSY', )


@block
def dispatcher(config, data_in: FifoConsumer, data_out: FifoProducer):
    """
    Logic to handle data stream read and write from / to cpu. Including dispatching single
    solver instances to solve a given ivp and collecting results to send back to cpu.
    :return:
    """
    assert data_in.clk == data_out.clk
    assert data_in.rst == data_out.rst
    clk = data_in.clk
    rst = data_in.rst

    state = Signal(t_state.IDLE)

    solver_input_desc = get_input_desc(config)
    solver_input = solver_input_desc.create_read_instance(data_in.data)

    solver_output_desc = get_output_desc(config)
    solver_output = solver_output_desc.create_write_instance()
    solver_output_packed = solver_output.packed()

    current_data_id = Signal(num.integer())
    solver = SolverInterface(config.system_size, flow=FlowControl(clk=clk))
    solver_inst = rk_solver(config, solver)

    @always_seq(clk.posedge, reset=None)
    def state_machine():
        if rst:
            data_out.wr.next = False
            data_in.rd.next = False
            solver.flow.enb.next = False
            solver.flow.rst.next = True
            state.next = t_state.IDLE
        else:
            if state == t_state.IDLE:
                data_out.wr.next = False
                solver.flow.rst.next = False

                solver.h.next = solver_input.h
                solver.n.next = solver_input.n
                solver.x_start.next = solver_input.x_start
                for i in range(config.system_size):
                    solver.y_start[i].next = solver_input.y_start[i]
                current_data_id.next = solver_output.id

                if not data_in.empty:
                    data_in.rd.next = True
                    solver.flow.enb.next = True
                    state.next = t_state.BUSY
            elif state == t_state.BUSY:
                data_in.rd.next = False

                solver_output.x.next = solver.x
                for i in range(config.system_size):
                    solver_output.y[i].next = solver.y[i]
                solver_output.id.next = current_data_id

                if solver.flow.fin:
                    data_out.wr.next = True
                    solver.flow.rst.next = True
                    state.next = t_state.IDLE

    @always_comb
    def assign_solver_output():
        data_out.data.next = solver_output_packed

    return instances()
