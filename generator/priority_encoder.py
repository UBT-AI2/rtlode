from myhdl import instances, block, SignalType, always_comb, Signal, ConcatSignal, intbv


@block
def priority_encoder_one_hot(
        in_vec: SignalType,
        out_vec: SignalType,
        index: SignalType = None
):
    """
    Highest order bit gets priority and is the only true in out_vec.
    :param in_vec: input vector
    :param out_vec: out vector one hot
    :param index: optional signal to get current index
    :return: myhdl instances
    """
    assert len(in_vec) == len(out_vec)

    bit_width = len(in_vec)
    if index is None:
        index = Signal(intbv(0)[bit_width:])

    @always_comb
    def assign_out():
        index.next = 0
        for i in range(bit_width):
            if in_vec[i]:
                index.next = i

    @always_comb
    def out_driver():
        if in_vec == 0:
            out_vec.next = 0
        else:
            out_vec.next = (1 << index)

    return instances()
