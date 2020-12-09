from enum import Enum
from typing import Union

import struct
from myhdl import intbv


class NumberFactory:
    def __init__(self, nbr_bits):
        self.nbr_bits = nbr_bits

    def create(self, val=0):
        return self.create_from_constant(self.create_constant(val))

    def create_from_constant(self, const_val):
        raise NotImplementedError

    def create_constant(self, val):
        raise NotImplementedError

    def value_of(self, val):
        raise NotImplementedError

    @staticmethod
    def from_config(numeric_cfg: dict):
        numeric_type = numeric_cfg.get('type', 'fixed')

        if numeric_type == 'fixed':
            return SignedFixedNumberFactory.from_config(numeric_cfg)
        elif numeric_type == 'floating':
            return FloatingNumberFactory.from_config(numeric_cfg)
        else:
            raise NotImplementedError('Unknwown numeric_type specified in config.')


class BoolNumberFactory(NumberFactory):
    def __init__(self):
        super().__init__(1)

    def create_from_constant(self, const_val):
        return bool(const_val)

    def create_constant(self, val):
        return bool(val)

    def value_of(self, val):
        return bool(val)

    @staticmethod
    def from_config(numeric_cfg: dict):
        raise NotImplementedError()


class IntegerNumberFactory(NumberFactory):
    def create_from_constant(self, const_val):
        return intbv(const_val, min=0, max=2 ** self.nbr_bits)

    def create_constant(self, val):
        return int(val)

    def value_of(self, val):
        return int(val)

    @staticmethod
    def from_config(numeric_cfg: dict):
        raise NotImplementedError()


class SignedFixedNumberFactory(NumberFactory):
    nonfraction_bits = None
    fraction_bits = None

    def __init__(self, fraction_size, nonfraction_size):
        self.fraction_bits = fraction_size
        self.nonfraction_bits = nonfraction_size
        super().__init__(1 + self.nonfraction_bits + self.fraction_bits)

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
        return SignedFixedNumberFactory(fraction_size, nonfraction_size)


class FloatingPrecission(Enum):
    SINGLE = 32
    DOUBLE = 64


class FloatingNumberFactory(NumberFactory):
    precission_struct_id_map = {
        FloatingPrecission.SINGLE: ('!I', '!f'),
        FloatingPrecission.DOUBLE: ('!Q', '!d')
    }

    def __init__(self, precission: Union[FloatingPrecission, str]):
        if isinstance(precission, str):
            precission = FloatingPrecission[precission.upper()]
        super().__init__(precission.value)

        self.precission = precission

    def create_from_constant(self, const_val):
        return intbv(const_val, min=0, max=2 ** self.nbr_bits)

    def create_constant(self, val):
        unpack_mod, pack_mod = self.precission_struct_id_map[self.precission]
        return struct.unpack(unpack_mod, struct.pack(pack_mod, val))[0]

    def value_of(self, val):
        pack_mod, unpack_mod = self.precission_struct_id_map[self.precission]
        return struct.unpack(unpack_mod, struct.pack(pack_mod, val))[0]

    @property
    def width_exp(self):
        if self.precission == FloatingPrecission.SINGLE:
            return 8
        elif self.precission == FloatingPrecission.DOUBLE:
            return 11
        else:
            raise NotImplementedError

    @property
    def width_man(self):
        if self.precission == FloatingPrecission.SINGLE:
            return 23
        elif self.precission == FloatingPrecission.DOUBLE:
            return 52
        else:
            raise NotImplementedError

    @staticmethod
    def from_config(numeric_cfg: dict):
        precission = FloatingPrecission[
            numeric_cfg.get('floating_precision', 'double').upper()
        ]
        return FloatingNumberFactory(precission)


"""
Numeric Type Handling

Use the method set_default() to set a default NumberFactory for the whole numeric logic.
The get_default() method is used by the logic to retrieve the type.
"""
default_factory = SignedFixedNumberFactory(37, 16)


def get_numeric_factory():
    return default_factory


def set_numeric_factory(number_type: NumberFactory):
    global default_factory
    default_factory = number_type


integer_factory = IntegerNumberFactory(32)


def get_integer_factory():
    return integer_factory


def set_integer_factory(number_type: IntegerNumberFactory):
    global integer_factory
    integer_factory = number_type


bool_factory = BoolNumberFactory()


def get_bool_factory():
    return bool_factory
