from myhdl import intbv

INTEGER_SIZE = 16
FRACTION_SIZE = 47
TOTAL_SIZE = 1 + INTEGER_SIZE + FRACTION_SIZE
MAX_VALUE = 2 ** (INTEGER_SIZE + FRACTION_SIZE) - 1
MIN_VALUE = - MAX_VALUE

DOUBLE_MAX_VALUE = 2 ** (2 * INTEGER_SIZE + 2 * FRACTION_SIZE) - 1
DOUBLE_MIN_VALUE = - DOUBLE_MAX_VALUE


def integer(val=0, max=2 ** 32):
    return intbv(val, min=0, max=max)


bool = bool


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
