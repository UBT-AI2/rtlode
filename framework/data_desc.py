from bitarray import bitarray
from myhdl import intbv

from framework.packed_struct import StructDescription, BitVector, StructDescriptionMetaclass, field_len
from utils import num


def get_input_desc(system_size):
    integer_type = num.UnsignedIntegerNumberType(32)
    default_type = num.get_default_type()
    len_without_padding = 2 * integer_type.nbr_bits + (2 + system_size) * default_type.nbr_bits
    if len_without_padding % 8 != 0:
        len_padding = 8 - len_without_padding % 8

        class InputData(StructDescription, metaclass=StructDescriptionMetaclass):
            id = BitVector(integer_type)
            x_start = BitVector(default_type)
            y_start = [BitVector(default_type) for _ in range(system_size)]
            h = BitVector(default_type)
            n = BitVector(integer_type)
            _bit_padding = BitVector(len_padding)
    else:
        len_padding = 0

        class InputData(StructDescription, metaclass=StructDescriptionMetaclass):
            id = BitVector(integer_type)
            x_start = BitVector(default_type)
            y_start = [BitVector(default_type) for _ in range(system_size)]
            h = BitVector(default_type)
            n = BitVector(integer_type)

    assert (len_without_padding + len_padding) % 8 == 0
    assert len(InputData) == len_without_padding + len_padding

    return InputData


def _data_to_bitarray(field_desc, data):
    if isinstance(field_desc, BitVector):
        nbr_bits = field_len(field_desc)
        value = intbv(data)[nbr_bits:0]
        value_bits = bitarray([value[i] for i in range(nbr_bits)])
        return value_bits
    elif isinstance(field_desc, list):
        list_bits = bitarray()
        for i, el in enumerate(field_desc):
            list_bits += _data_to_bitarray(el, data[i])
        return list_bits
    else:
        raise NotImplementedError()


def pack_input_data(system_size, input_data: dict) -> bytes:
    input_desc = get_input_desc(system_size)
    data = bitarray(endian='little')

    for field_name, field_desc in reversed(input_desc.get_fields().items()):
        nbr_bits = field_len(field_desc)
        if field_name in input_data:
            value_bits = _data_to_bitarray(field_desc, input_data[field_name])
        else:
            value_bits = bitarray(nbr_bits)
            value_bits.setall(0)

        data += value_bits

    assert len(data) == field_len(input_desc)

    return data.tobytes()


def get_output_desc(system_size):
    integer_type = num.UnsignedIntegerNumberType(32)
    default_type = num.get_default_type()
    len_without_padding = integer_type.nbr_bits + (1 + system_size) * default_type.nbr_bits
    if len_without_padding % 8 != 0:
        len_padding = 8 - len_without_padding % 8

        class OutputData(StructDescription, metaclass=StructDescriptionMetaclass):
            id = BitVector(integer_type)
            x = BitVector(default_type)
            y = [BitVector(default_type) for _ in range(system_size)]
            _bit_padding = BitVector(len_padding)

    else:
        len_padding = 0

        class OutputData(StructDescription, metaclass=StructDescriptionMetaclass):
            id = BitVector(integer_type)
            x = BitVector(default_type)
            y = [BitVector(default_type) for _ in range(system_size)]

    assert (len_without_padding + len_padding) % 8 == 0
    assert len(OutputData) == len_without_padding + len_padding

    return OutputData


def _bitarray_to_data(field_desc, data_bits):
    if isinstance(field_desc, BitVector):
        nbr_bits = field_len(field_desc)
        value = intbv(0)[nbr_bits:0]
        for i in range(nbr_bits):
            value[i] = data_bits[i]
        return value
    elif isinstance(field_desc, list):
        value_list = []
        offset = 0
        for el in field_desc:
            nbr_bits = field_len(el)
            el_bits = data_bits[offset:offset + nbr_bits]
            value_list.append(_bitarray_to_data(el, el_bits))
            offset += nbr_bits
        assert offset == field_len(field_desc)
        return value_list
    else:
        raise NotImplementedError()


def unpack_output_data(system_size, output_data: bytes) -> dict:
    output_desc = get_output_desc(system_size)
    data = bitarray(endian='little')
    data.frombytes(output_data)

    assert len(data) == field_len(output_desc)

    unpacked_data = {}

    offset = 0
    for field_name, field_desc in reversed(output_desc.get_fields().items()):
        nbr_bits = field_len(field_desc)
        value_bits = data[offset:offset + nbr_bits]

        unpacked_data[field_name] = _bitarray_to_data(field_desc, value_bits)

        offset += nbr_bits

    return unpacked_data
