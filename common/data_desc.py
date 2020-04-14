from common.packed_struct import StructDescription, BitVector, List
from utils import num


def get_input_desc(config):
    class InputData(StructDescription):
        x_start = BitVector(num.TOTAL_SIZE)
        y_start = List(config.system_size, BitVector(num.TOTAL_SIZE))
        h = BitVector(num.TOTAL_SIZE)
        n = BitVector(num.INTEGER_SIZE)
        id = BitVector(num.INTEGER_SIZE)

    return InputData


def get_output_desc(config):
    class OutputData(StructDescription):
        x = BitVector(num.TOTAL_SIZE)
        y = List(config.system_size, BitVector(num.TOTAL_SIZE))
        id = BitVector(num.INTEGER_SIZE)

    return OutputData
