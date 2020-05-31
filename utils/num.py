from myhdl import intbv, modbv, SignalType

INTEGER_SIZE = 32

# Define globals at module level
NONFRACTION_SIZE = None
FRACTION_SIZE = None

TOTAL_SIZE = None
MAX_VALUE = None
MIN_VALUE = None


def from_config(numeric_cfg: dict):
    global FRACTION_SIZE, NONFRACTION_SIZE
    FRACTION_SIZE = numeric_cfg.get('fixed_point_fraction_size', 37)
    NONFRACTION_SIZE = numeric_cfg.get('fixed_point_nonfraction_size', 16)
    # Recalculate dependent values
    global TOTAL_SIZE, MAX_VALUE, MIN_VALUE
    TOTAL_SIZE = 1 + NONFRACTION_SIZE + FRACTION_SIZE
    MAX_VALUE = 2 ** (NONFRACTION_SIZE + FRACTION_SIZE)
    MIN_VALUE = - MAX_VALUE


# Initialize globals
from_config({})


def integer(val=0, max=2 ** INTEGER_SIZE):
    return intbv(val, min=0, max=max)


bool = bool


def default(val=0):
    return intbv(val, min=MIN_VALUE, max=MAX_VALUE)


def same_as(signal: SignalType, val=0):
    if isinstance(signal.val, modbv):
        return modbv(val, min=signal.min, max=signal.max)
    elif isinstance(signal.val, intbv):
        return intbv(val, min=signal.min, max=signal.max)
    else:
        raise NotImplemented()


def int_from_float(float_val):
    return int(round(float_val * 2 ** FRACTION_SIZE))


def from_float(float_val, size=None):
    raw = int_from_float(float_val)
    if size is not None:
        return same_as(size, val=raw)
    return default(raw)


def to_float(fixed_val):
    if fixed_val < 0:
        return -(float(-fixed_val) / 2 ** FRACTION_SIZE)
    else:
        return float(fixed_val) / 2 ** FRACTION_SIZE
