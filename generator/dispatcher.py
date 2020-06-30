from myhdl import block, Signal, instances, always_comb, intbv, ConcatSignal, always

from generator.config import Config
from generator.cdc_utils import AsyncFifoConsumer, AsyncFifoProducer
from generator.fifo import FifoProducer, FifoConsumer, fifo
from generator.priority_encoder import priority_encoder_one_hot
from generator.solver import solver
from generator.utils import clone_signal


@block
def solver_driver(clk, rst,
                  rdy_signal, rdy_ack, data_in, fifo_producer,
                  fin_signal, fin_ack, data_out, data_out_data, fifo_consumer):

    @always(clk.posedge)
    def assign_data_in():
        if rst:
            fifo_producer.wr.next = False
            rdy_signal.next = True
        else:
            if data_in.rd and not data_in.empty and rdy_ack:
                fifo_producer.data.next = data_in.data
                fifo_producer.wr.next = True
                rdy_signal.next = False
            elif fifo_producer.wr and not fifo_producer.full:
                fifo_producer.wr.next = False
                rdy_signal.next = True

    @always(clk.posedge)
    def assign_data_out():
        if rst:
            fifo_consumer.rd.next = True
            fin_signal.next = False
        else:
            if fifo_consumer.rd and not fifo_consumer.empty:
                data_out_data.next = fifo_consumer.data
                fin_signal.next = True
                fifo_consumer.rd.next = False
            elif data_out.wr and not data_out.full and fin_ack:
                fin_signal.next = False
                fifo_consumer.rd.next = True

    return instances()


@block
def dispatcher(config: Config, data_in: AsyncFifoConsumer, data_out: AsyncFifoProducer):
    """
    Logic to handle data stream read and write from / to cpu. Including dispatching single
    solver instances to solve a given ivp and collecting results to send back to cpu.
    :return: myhdl instances
    """
    assert data_in.clk == data_out.clk
    assert data_in.rst == data_out.rst
    clk = data_in.clk
    rst = data_in.rst

    rdy_signals = [Signal(bool(0)) for _ in range(config.nbr_solver)]
    rdy_signals_vec = ConcatSignal(*reversed(rdy_signals)) if config.nbr_solver > 1 else rdy_signals[0]
    rdy_priority = Signal(intbv(0)[config.nbr_solver:])
    fin_signals = [Signal(bool(0)) for _ in range(config.nbr_solver)]
    fin_signals_vec = ConcatSignal(*reversed(fin_signals)) if config.nbr_solver > 1 else fin_signals[0]
    fin_priority = Signal(intbv(0)[config.nbr_solver:])

    rdy_priority_encoder = priority_encoder_one_hot(rdy_signals_vec, rdy_priority)
    fin_priority_encoder = priority_encoder_one_hot(fin_signals_vec, fin_priority)

    solver_data_out = [clone_signal(data_out.data) for _ in range(config.nbr_solver)]

    solver_input_producers = [
        FifoProducer(clone_signal(data_in.data))
        for _ in range(config.nbr_solver)
    ]

    solver_input_consumers = [
        FifoConsumer(clone_signal(data_in.data))
        for _ in range(config.nbr_solver)
    ]

    solver_input_fifos = [
        fifo(clk, rst, solver_input_producers[i], solver_input_consumers[i], buffer_size_bits=2)
        for i in range(config.nbr_solver)
    ]

    solver_output_producers = [
        FifoProducer(clone_signal(data_out.data))
        for _ in range(config.nbr_solver)
    ]

    solver_output_consumers = [
        FifoConsumer(clone_signal(data_out.data))
        for _ in range(config.nbr_solver)
    ]

    solver_output_fifos = [
        fifo(clk, rst, solver_output_producers[i], solver_output_consumers[i], buffer_size_bits=2)
        for i in range(config.nbr_solver)
    ]

    solver_inst = [
        solver(config, clk, rst,
               data_in=solver_input_consumers[i],
               data_out=solver_output_producers[i])
        for i in range(config.nbr_solver)
    ]

    @always_comb
    def rd_driver():
        data_in.rd.next = rdy_priority != 0

    @always_comb
    def wr_driver():
        data_out.wr.next = fin_priority != 0

    solver_wrapper_inst = [
        solver_driver(clk, rst,
                      rdy_signals[i], rdy_priority(i), data_in, solver_input_producers[i],
                      fin_signals[i], fin_priority(i), data_out, solver_data_out[i], solver_output_consumers[i])
        for i in range(config.nbr_solver)
    ]

    @always_comb
    def assign_data_out():
        for i in range(config.nbr_solver):
            if fin_priority[i]:
                data_out.data.next = solver_data_out[i]

    return instances()
