from myhdl import block, always_seq, always, Signal, ResetSignal

from generator.utils import clone_signal

# TODO Add missing unit tests


@block
def assign(clk, rst, out_val, in_val):
    """
    Sequential assign.
    :param clk: clk
    :param rst: rst
    :param out_val: output
    :param in_val: input
    :return:
    """
    @always_seq(clk.posedge, reset=rst)
    def _assign():
        out_val.next = in_val
    return _assign


@block
def ff_synchronizer(clk, rst, chain_out, chain_in, stages=2, chain_rst_value=0):
    """
    Flip-Flop based synchronizer. Can be used to stabelize signals which are crossing clock domains.
    Generates a chain with ff_stages flip flops.
    :param clk: clock for the flip flops
    :param rst: reset for the flip flops
    :param chain_out: output signal of the chain
    :param chain_in: input signal of the chain
    :param stages: number of flip flops in the chain
    :param chain_rst_value: reset value for the flip flops
    :return: myhdl instances
    """
    ff_values = [chain_in, *[clone_signal(chain_in, value=chain_rst_value) for _ in range(stages - 1)], chain_out]
    return [
        assign(clk, rst, ff_values[stage_index + 1], ff_values[stage_index])
        for stage_index in range(stages)
    ]


@block
def areset_synchronizer(clk, async_rst, sync_rst, min_reset_cycles=2):
    """
    Synchronizer for async reset signals. Uses internally a flip-flop sychronizer.
    :param clk: clock of target domain
    :param async_rst: async reset signal to be synchonized
    :param sync_rst: sync reset signal
    :param min_reset_cycles: min clock cycles the sychronized reset should be high
    :return: myhdl instances
    """
    driver_val = Signal(bool(1))
    rst = ResetSignal(True, True, True)

    ff_inst = ff_synchronizer(clk, rst, sync_rst, driver_val, stages=min_reset_cycles, chain_rst_value=1)

    @always(clk.posedge, async_rst.posedge)
    def synchronize():
        if async_rst:
            rst.next = True
            driver_val.next = 1
        else:
            rst.next = False
            driver_val.next = 0

    return [ff_inst, synchronize]
