from framework.pipeline import PipeNumeric
from utils import num
import framework.pipeline_elements_fixed as elements_fixed
import framework.pipeline_elements_floating as elements_floating


def mul(a: PipeNumeric, b: PipeNumeric) -> PipeNumeric:
    """
    Pipeline node which multiplies the two given parameters.
    :param a: parameter a
    :param b: parameter b
    :return: PipeNumeric
    """
    if a.get_type() == b.get_type():
        number_type = a.get_type()
        if isinstance(number_type, num.FloatingNumberType):
            return elements_floating.mul(a, b)
        elif isinstance(number_type, num.SignedFixedNumberType):
            return elements_fixed.mul(a, b)
        else:
            raise NotImplementedError('Unknown numeric number type used.')
    else:
        raise NotImplementedError('Using numeric functions with parameters of different NumberTypes is not supported.')


def add(a: PipeNumeric, b: PipeNumeric) -> PipeNumeric:
    """
    Pipeline node which adds the two given parameters.
    :param a: parameter a
    :param b: parameter b
    :return: PipeNumeric
    """
    if a.get_type() == b.get_type():
        number_type = a.get_type()
        if isinstance(number_type, num.FloatingNumberType):
            return elements_floating.add(a, b)
        elif isinstance(number_type, num.SignedFixedNumberType) \
                or isinstance(number_type, num.UnsignedIntegerNumberType):
            return elements_fixed.add(a, b)
        else:
            raise NotImplementedError('Unknown numeric number type used.')
    else:
        raise NotImplementedError('Using numeric functions with parameters of different NumberTypes is not supported.')


def sub(a: PipeNumeric, b: PipeNumeric) -> PipeNumeric:
    """
    Pipeline node which subtracts b from a.
    :param a: parameter a
    :param b: parameter b
    :return: PipeNumeric
    """
    if a.get_type() == b.get_type():
        number_type = a.get_type()
        if isinstance(number_type, num.FloatingNumberType):
            return elements_floating.sub(a, b)
        elif isinstance(number_type, num.SignedFixedNumberType):
            return elements_fixed.sub(a, b)
        else:
            raise NotImplementedError('Unknown numeric number type used.')
    else:
        raise NotImplementedError('Using numeric functions with parameters of different NumberTypes is not supported.')


def negate(val: PipeNumeric) -> PipeNumeric:
    """
    Pipeline node which negates the given parameter.
    :param val: parameter val
    :return: PipeNumeric
    """
    number_type = val.get_type()

    if isinstance(number_type, num.SignedFixedNumberType):
        return elements_fixed.negate(val)
    elif isinstance(number_type, num.FloatingNumberType):
        return elements_floating.negate(val)
    else:
        raise NotImplementedError('Unknown numeric number typ used.')
