from myhdl import block, always_seq, Signal, instances, always_comb, intbv, ConcatSignal

from common import data_desc
from common.config import Config
from common.packed_struct import BitVector
from generator.cdc_utils import AsyncFifoConsumer, AsyncFifoProducer
from generator.priority_encoder import priority_encoder_one_hot
from generator.solver import solver


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

    solver_outputs = [
        BitVector(len(data_desc.get_output_desc(config.system_size))).create_instance()
        for _ in range(config.nbr_solver)
    ]

    solver_inst = [
        solver(config, clk, rst,
               data_in=data_in,
               data_out=AsyncFifoProducer(clk, rst, solver_outputs[i], data_out.wr, data_out.full),
               rdy=rdy_signals[i],
               rdy_ack=rdy_priority(i),
               fin=fin_signals[i],
               fin_ack=fin_priority(i))
        for i in range(config.nbr_solver)
    ]

    @always_seq(clk.posedge, reset=None)
    def fifo_handler():
        if rst:
            data_out.wr.next = False
            data_in.rd.next = False
        else:
            data_in.rd.next = False
            if rdy_signals_vec:
                if not data_in.rd:
                    data_in.rd.next = True
                elif not data_in.empty:
                    # One solver dispatched
                    if rdy_signals_vec != rdy_priority:
                        # More than one solver was ready
                        data_in.rd.next = True

            data_out.wr.next = False
            if fin_signals_vec:
                if not data_out.wr:
                    data_out.wr.next = True
                elif not data_out.full:
                    # Wrote one result back
                    if fin_signals_vec != fin_priority:
                        # More than one solver was finished
                        data_out.wr.next = True

    @always_comb
    def assign_data_out():
        for i in range(config.nbr_solver):
            if fin_priority[i]:
                data_out.data.next = solver_outputs[i]

    return instances()
