from enum import Enum
from typing import Union

import struct
from myhdl import intbv


class NumberType:
    def __init__(self, nbr_bits, signed=False):
        self.nbr_bits = nbr_bits
        self.signed = signed

    def __eq__(self, other):
        raise NotImplementedError

    def create(self, val=0):
        return self.create_from_constant(self.create_constant(val))

    def create_from_constant(self, const_val):
        """
        Create a myhdl type of correct size with initial value of const_val.
        Const_val must be in correct const representation (see create_constant).
        :param const_val: constant value
        :return: myhdl intbv with correct size (min, max) and initial value of const_val
        """
        raise NotImplementedError

    def create_constant(self, val):
        """
        Creates a constant representation of a python val.
        :param val: python value
        :return: constant representation usable in myhdl
        """
        raise NotImplementedError

    def value_of(self, val):
        raise NotImplementedError

    @staticmethod
    def from_config(numeric_cfg: dict):
        numeric_type = numeric_cfg.get('type', 'fixed')

        if numeric_type == 'fixed':
            return SignedFixedNumberType.from_config(numeric_cfg)
        elif numeric_type == 'floating':
            return FloatingNumberType.from_config(numeric_cfg)
        else:
            raise NotImplementedError('Unknwown numeric_type specified in config.')


class BoolNumberType(NumberType):
    def __init__(self):
        super().__init__(1)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return True
        raise NotImplementedError

    def create_from_constant(self, const_val):
        return bool(const_val)

    def create_constant(self, val):
        return bool(val)

    def value_of(self, val):
        return bool(val)

    @staticmethod
    def from_config(numeric_cfg: dict):
        raise NotImplementedError()


class UnsignedIntegerNumberType(NumberType):
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.nbr_bits == other.nbr_bits
        raise NotImplementedError

    def create_from_constant(self, const_val):
        return intbv(const_val, min=0, max=2 ** self.nbr_bits)

    def create_constant(self, val):
        return int(val)

    def value_of(self, val):
        return int(val)

    @staticmethod
    def from_config(numeric_cfg: dict):
        raise NotImplementedError()


class SignedFixedNumberType(NumberType):
    nonfraction_bits = None
    fraction_bits = None

    def __init__(self, fraction_size, nonfraction_size):
        self.fraction_bits = fraction_size
        self.nonfraction_bits = nonfraction_size
        super().__init__(1 + self.nonfraction_bits + self.fraction_bits, signed=True)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.fraction_bits == other.fraction_bits and self.nonfraction_bits == other.nonfraction_bits
        raise NotImplementedError

    def create_from_constant(self, const_val):
        max_value = 2 ** (self.nonfraction_bits + self.fraction_bits)
        return intbv(const_val, min=-max_value, max=max_value)

    def create_constant(self, val):
        return int(round(val * 2 ** self.fraction_bits))

    def value_of(self, val):
        if val < 0:
            return -(float(-val) / 2 ** self.fraction_bits)
        else:
            return float(val) / 2 ** self.fraction_bits

    @staticmethod
    def from_config(numeric_cfg: dict):
        fraction_size = numeric_cfg.get('fixed_point_fraction_size', 37)
        nonfraction_size = numeric_cfg.get('fixed_point_nonfraction_size', 16)
        return SignedFixedNumberType(fraction_size, nonfraction_size)


class FloatingPrecision(Enum):
    SINGLE = 32
    DOUBLE = 64


class FloatingNumberType(NumberType):
    precision_struct_id_map = {
        FloatingPrecision.SINGLE: ('!I', '!f'),
        FloatingPrecision.DOUBLE: ('!Q', '!d')
    }

    def __init__(self, precision: Union[FloatingPrecision, str]):
        if isinstance(precision, str):
            precision = FloatingPrecision[precision.upper()]
        super().__init__(precision.value)

        self.precision = precision

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.precision == other.precision
        raise NotImplementedError

    def create_from_constant(self, const_val):
        return intbv(const_val, min=0, max=2 ** self.nbr_bits)

    def create_constant(self, val):
        unpack_mod, pack_mod = self.precision_struct_id_map[self.precision]
        return struct.unpack(unpack_mod, struct.pack(pack_mod, val))[0]

    def value_of(self, val):
        pack_mod, unpack_mod = self.precision_struct_id_map[self.precision]
        return struct.unpack(unpack_mod, struct.pack(pack_mod, val))[0]

    @staticmethod
    def from_config(numeric_cfg: dict):
        precision = FloatingPrecision[
            numeric_cfg.get('floating_precision', 'double').upper()
        ]
        return FloatingNumberType(precision)


"""
Numeric Type Handling

Use the method set_default() to set a default NumberFactory for the whole numeric logic.
The get_default() method is used by the logic to retrieve the type.
"""
default_type = SignedFixedNumberType(37, 16)


def get_default_type():
    return default_type


def set_default_type(number_type: NumberType):
    global default_type
    default_type = number_type
