from common.packed_struct import StructDescription, BitVector, List, StructDescriptionMetaclass
from utils import num


def get_input_desc(system_size):
    len_without_padding = 2 * num.INTEGER_SIZE + (2 + system_size) * num.TOTAL_SIZE
    if len_without_padding % 8 != 0:
        len_padding = 8 - len_without_padding % 8

        class InputData(StructDescription, metaclass=StructDescriptionMetaclass):
            id = BitVector(num.INTEGER_SIZE)
            x_start = BitVector(num.TOTAL_SIZE)
            y_start = List(system_size, BitVector(num.TOTAL_SIZE))
            h = BitVector(num.TOTAL_SIZE)
            n = BitVector(num.INTEGER_SIZE)
            _bit_padding = BitVector(len_padding)
    else:
        len_padding = 0

        class InputData(StructDescription, metaclass=StructDescriptionMetaclass):
            id = BitVector(num.INTEGER_SIZE)
            x_start = BitVector(num.TOTAL_SIZE)
            y_start = List(system_size, BitVector(num.TOTAL_SIZE))
            h = BitVector(num.TOTAL_SIZE)
            n = BitVector(num.INTEGER_SIZE)

    assert (len_without_padding + len_padding) % 8 == 0
    assert len(InputData) == len_without_padding + len_padding

    return InputData


def get_output_desc(system_size):
    len_without_padding = num.INTEGER_SIZE + (1 + system_size) * num.TOTAL_SIZE
    if len_without_padding % 8 != 0:
        len_padding = 8 - len_without_padding % 8

        class OutputData(StructDescription, metaclass=StructDescriptionMetaclass):
            id = BitVector(num.INTEGER_SIZE)
            x = BitVector(num.TOTAL_SIZE)
            y = List(system_size, BitVector(num.TOTAL_SIZE))
            _bit_padding = BitVector(len_padding)

    else:
        len_padding = 0

        class OutputData(StructDescription, metaclass=StructDescriptionMetaclass):
            id = BitVector(num.INTEGER_SIZE)
            x = BitVector(num.TOTAL_SIZE)
            y = List(system_size, BitVector(num.TOTAL_SIZE))

    assert (len_without_padding + len_padding) % 8 == 0
    assert len(OutputData) == len_without_padding + len_padding

    return OutputData
