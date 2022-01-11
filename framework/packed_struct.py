import inspect

import collections
from typing import Union

from myhdl import Signal, intbv, SignalType, ConcatSignal, block

from utils.num import NumberType


def field_len(field):
    if isinstance(field, list):
        length = 0
        for subfield in field:
            length += field_len(subfield)
        return length
    return len(field)


class _PackedStruct:
    def __init__(self, fields):
        self._fields = fields
        for name, value in fields.items():
            setattr(self, name, value)

    def __len__(self):
        nbr_bits = 0
        for name in self._fields:
            nbr_bits += field_len(self._fields[name])
        return nbr_bits


class PackedReadStruct(_PackedStruct):
    """
    Used to describe a read instance of a StructDescription.
    """
    @staticmethod
    def _definition_to_signal(definition, data, high_index, low_index):
        if isinstance(definition, BitVector):
            return definition.create_read_instance(data, high_index, low_index)
        elif isinstance(definition, list):
            vector = []
            instances = []
            for el in definition:
                low_index = high_index - len(el)
                inst, sign = PackedReadStruct._definition_to_signal(el, data, high_index, low_index)
                vector.append(sign)
                instances.extend(inst)
                high_index = low_index
            return instances, vector
        elif issubclass(definition, StructDescription):
            sub_struct = PackedReadStruct.create(definition.get_fields(), data, high_index, low_index)
            return sub_struct._instance_desc, sub_struct

    @staticmethod
    def create(fields, data, high_lim, low_lim):
        instance_desc = []

        high_index = high_lim
        for name, value in fields.items():
            low_index = high_index - field_len(value)
            if low_index < low_lim:
                raise Exception('PackedReadStruct trying to access data below lower limit.')
            field_instances, fields[name] = PackedReadStruct._definition_to_signal(value, data, high_index, low_index)
            instance_desc.extend(field_instances)
            high_index = low_index

        return PackedReadStruct(fields, data, high_lim, low_lim, instance_desc)

    def __init__(self, fields, data, high_lim, low_lim, instance_desc):
        self._data = data
        self._high_lim = high_lim
        self._low_lim = low_lim
        self._instance_desc = instance_desc

        super().__init__(fields)

    def high_lim(self):
        return self._high_lim

    def low_lim(self):
        return self._low_lim

    @block
    def instances(self):
        return [logic(*parameter) for logic, parameter in self._instance_desc]


class PackedWriteStruct(_PackedStruct):
    """
    Used to describe a write instance of a StructDescription.
    """
    @staticmethod
    def _definition_to_field(value):
        if isinstance(value, BitVector):
            return value.create_instance()
        elif isinstance(value, list):
            return [PackedWriteStruct._definition_to_field(el) for el in value]
        elif issubclass(value, StructDescription):
            return value.create_write_instance()
        raise Exception('Unsupported field type in StructDescription.')

    @staticmethod
    def _update_field(value):
        if isinstance(value, SignalType):
            value._update()
        elif isinstance(value, list):
            for el in value:
                PackedWriteStruct._update_field(el)
        elif isinstance(value, PackedWriteStruct):
            value.update()
        else:
            raise Exception('Unsupported field type in PackedWriteStruct obj.')

    def __init__(self, fields):
        for name, value in fields.items():
            fields[name] = PackedWriteStruct._definition_to_field(value)
        super().__init__(fields)

    def packed(self):
        """
        Returns a ConcatSignal following the signals of the struct.
        :return: concatted signal
        """
        signal_list = PackedWriteStruct.create_signal_list(list(self._fields.values()))
        return PackedWriteStruct.concat_signal_list(signal_list)

    @staticmethod
    def concat_signal_list(signal_list):
        if len(signal_list) == 0:
            raise Exception('Empty PackedSignals obj.')
        elif len(signal_list) == 1:
            return signal_list[0]
        else:
            return ConcatSignal(*signal_list)

    @staticmethod
    def create_signal_list(value):
        if isinstance(value, SignalType):
            return [value]
        elif isinstance(value, list):
            vector = []
            for el in value:
                vector.extend(PackedWriteStruct.create_signal_list(el))
            return vector
        elif isinstance(value, PackedWriteStruct):
            vector = []
            for el in value._fields.values():
                vector.extend(PackedWriteStruct.create_signal_list(el))
            return vector
        else:
            raise Exception('Unsupported field type in PackedWriteStruct obj.')

    def update(self):
        """
        Updates all internal Signals.
        :return:
        """
        for _, value in self._fields.items():
            PackedWriteStruct._update_field(value)


class BitVector:
    """
    Can be used to describe a bitfield in a StructDescription.
    """
    def __init__(self, size_or_type: Union[NumberType, int]):
        self._size_or_type = size_or_type

    def __len__(self):
        if isinstance(self._size_or_type, NumberType):
            return self._size_or_type.nbr_bits
        return self._size_or_type

    def create_instance(self):
        """
        Creates a signal which can be used as representation of given BitVector.
        :return: signal representation
        """
        if isinstance(self._size_or_type, NumberType):
            return Signal(self._size_or_type.create())
        return Signal(intbv(0)[self._size_or_type:0])

    def create_read_instance(self, data, high_index, low_index):
        if isinstance(self._size_or_type, NumberType) and self._size_or_type.signed:
            signed_data = self.create_instance()
            from generator.utils import reinterpret_as_signed
            return [(reinterpret_as_signed, (data(high_index, low_index), signed_data))], signed_data
        return [], data(high_index, low_index)


class StructDescriptionMetaclass(type):
    """
    Internal metaclass allowing the use of len() on StructDescription classes.
    """
    def __len__(self):
        return self.len()

    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(mcs, name, bases, classdict):
        classdict['__ordered__'] = list(classdict.keys())
        return type.__new__(mcs, name, bases, classdict)


class StructDescription(metaclass=StructDescriptionMetaclass):
    """
    Used to describe a PackedStructure.
    Class attributes can either be a BitVector or other StructDescriptions.

    As Example:
        class CcipRx(StructDescription):
            c0TxAlmFull = BitVector(1)
            c1TxAlmFull = BitVector(1)
            c0 = CcipC0Rx
            c1 = CcipC1Rx
    """
    @classmethod
    def from_kwargs(cls, name, **kwargs):
        return StructDescriptionMetaclass(name, (StructDescription, ), kwargs)

    @classmethod
    def len(cls):
        """
        Returns the number of bits of the descripted struct.
        :return: number of bits
        """
        cls._check_wellformness()
        length = 0
        for value in cls.get_fields().values():
            length += field_len(value)
        return length

    @classmethod
    def get_fields(cls):
        return collections.OrderedDict([(k, getattr(cls, k)) for k in cls.__ordered__ if not k.startswith("__")])

    @staticmethod
    def _is_field_wellformed(field):
        if isinstance(field, BitVector):
            return True
        elif isinstance(field, list):
            wellformed = True
            for el in field:
                wellformed = wellformed and StructDescription._is_field_wellformed(el)
            return wellformed
        elif inspect.isclass(field) and issubclass(field, StructDescription):
            wellformed = True
            for el in field.get_fields().values():
                wellformed = wellformed and StructDescription._is_field_wellformed(el)
            return wellformed
        return False

    @classmethod
    def _check_wellformness(cls):
        for field in cls.get_fields().values():
            if not StructDescription._is_field_wellformed(field):
                raise Exception('Unsupported field type in StructDescription.')
        return True

    @classmethod
    def create_read_instance(cls, data: SignalType, high_lim=None, low_lim=None) -> PackedReadStruct:
        """
        Creates a read instance of a described structure. YOU MUST call the instances() method on the result and take
        care that they are known to myhdl.
        :param data: raw data to be mapped on struct
        :param high_lim: Upper limit for data access
        :param low_lim: Lower limit for data access
        :return: nested struct following the described structure
        """
        if not isinstance(data, PackedReadStruct)\
                and (not isinstance(data, SignalType) or not isinstance(data.val, intbv)):
            raise Exception('PackedReadStruct data must be of type intbv.')
        cls._check_wellformness()

        if not high_lim:
            if isinstance(data, PackedReadStruct):
                high_lim = data.high_lim()
            else:
                high_lim = len(data)
        if not low_lim:
            if isinstance(data, PackedReadStruct):
                low_lim = data.low_lim()
            else:
                low_lim = 0

        if isinstance(data, PackedReadStruct):
            data = data._data

        if high_lim - low_lim != len(cls):
            raise Exception('PackedReadStruct data must be the size of StructDescription.')
        return PackedReadStruct.create(cls.get_fields(), data, high_lim, low_lim)

    @classmethod
    def create_write_instance(cls) -> PackedWriteStruct:
        """
        Creates a writable instance of the described structure.
        :return: nested struct following the described structure
        """
        cls._check_wellformness()

        return PackedWriteStruct(cls.get_fields())
