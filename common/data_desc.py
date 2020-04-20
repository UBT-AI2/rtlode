from common.packed_struct import StructDescription, BitVector, List, StructDescriptionMetaclass
from utils import num


def get_input_desc(system_size):
    class InputData(StructDescription, metaclass=StructDescriptionMetaclass):
        x_start = BitVector(num.TOTAL_SIZE)
        y_start = List(system_size, BitVector(num.TOTAL_SIZE))
        h = BitVector(num.TOTAL_SIZE)
        n = BitVector(num.INTEGER_SIZE)
        id = BitVector(num.INTEGER_SIZE)

    return InputData


def get_output_desc(system_size):
    class OutputData(StructDescription, metaclass=StructDescriptionMetaclass):
        x = BitVector(num.TOTAL_SIZE)
        y = List(system_size, BitVector(num.TOTAL_SIZE))
        id = BitVector(num.INTEGER_SIZE)

    return OutputData
