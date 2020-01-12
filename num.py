from myhdl import intbv, block, always_seq, instances, always_comb, Signal

INTEGER_SIZE = 64
FRACTION_SIZE = 64
MAX_VALUE = 2**(INTEGER_SIZE + FRACTION_SIZE) - 1
MIN_VALUE = - MAX_VALUE

DOUBLE_MAX_VALUE = 2**(2 * INTEGER_SIZE + 2 * FRACTION_SIZE) - 1
DOUBLE_MIN_VALUE = - DOUBLE_MAX_VALUE


def integer(val=0, max=2 ** 32 - 1):
    return intbv(val, min=0, max=max)


def default(val=0):
    return intbv(val, min=MIN_VALUE, max=MAX_VALUE)


def same_as(signal, val=0):
    return intbv(val, min=signal.min, max=signal.max)


def from_float(float_val, sig=None):
    raw = int(round(float_val * 2 ** FRACTION_SIZE))
    if sig is not None:
        return same_as(sig, val=raw)
    return default(raw)


def to_float(fixed_val):
    if fixed_val < 0:
        return -(float(-fixed_val) / 2 ** FRACTION_SIZE)
    else:
        return float(fixed_val) / 2 ** FRACTION_SIZE


@block
def add(in_a, in_b, out_c, clk=None):
    def calc():
        out_c.next = in_a + in_b

    if clk is not None:
        calc = always_seq(clk.posedge, reset=None)(calc)
    else:
        calc = always_comb(calc)
    return calc


@block
def sub(in_a, in_b, out_c, clk=None):
    def calc():
        out_c.next = in_a - in_b

    if clk is not None:
        calc = always_seq(clk.posedge, reset=None)(calc)
    else:
        calc = always_comb(calc)
    return calc


@block
def mul(in_a, in_b, out_c, clk=None):
    reg = Signal(intbv(0, min=DOUBLE_MIN_VALUE, max=DOUBLE_MAX_VALUE))

    @always_comb
    def resize():
        out_c.next = reg[INTEGER_SIZE + FRACTION_SIZE + 1 + FRACTION_SIZE:FRACTION_SIZE].signed()

    def calc():
        reg.next = (in_a * in_b)

    if clk is not None:
        calc = always_seq(clk.posedge, reset=None)(calc)
        return [resize, calc]
    else:
        calc = always_comb(calc)
        return [resize, calc]
