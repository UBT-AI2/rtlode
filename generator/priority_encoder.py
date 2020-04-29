from myhdl import instances, block, SignalType, always_comb, Signal, ConcatSignal


@block
def highest_bit_checker(
        in_vec: SignalType,
        out_bit: SignalType,
        index
):
    @always_comb
    def check():
        if in_vec[index] and in_vec[:index + 1] == 0:
            out_bit.next = True
        else:
            out_bit.next = False

    return instances()


@block
def priority_encoder_one_hot(
        in_vec: SignalType,
        out_vec: SignalType
):
    """
    Highest order bit gets priority and outputed in out_vec.
    :param in_vec: input vector
    :param out_vec: out vector one hot
    :return: myhdl instances
    """
    assert len(in_vec) == len(out_vec)

    bit_width = len(in_vec)
    priority_bits = [Signal(bool(0)) for _ in range(bit_width)]
    priority_vec = ConcatSignal(*reversed(priority_bits)) if bit_width > 1 else priority_bits[0]

    in_vec_highest_bit = in_vec(bit_width - 1) if bit_width > 1 else in_vec
    priority_highest_bit = priority_bits[bit_width - 1]

    @always_comb
    def highest_index():
        if in_vec_highest_bit:
            priority_highest_bit.next = True
        else:
            priority_highest_bit.next = False

    other_indeces = [
        highest_bit_checker(in_vec, priority_bits[i], i) for i in range(bit_width - 1)
    ]

    @always_comb
    def assign_out():
        out_vec.next = priority_vec

    return instances()
