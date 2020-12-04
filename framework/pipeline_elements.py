from utils import num
import framework.pipeline_elements_fixed as elements_fixed
import framework.pipeline_elements_floating as elements_floating


def mul(a, b):
    """
    Pipeline node which multiplies the two given parameters.
    Optimization is performed where possible.
    The return type is int if both parameters were integer and so the result is static. Depending of the multiplication
    implementation used the return type is CombNode or SeqNode in other cases.
    :param a: parameter a
    :param b: parameter b
    :return: int or pipeline node
    """
    num_factory = num.get_numeric_factory()

    if isinstance(num_factory, num.SignedFixedNumberFactory):
        return elements_fixed.mul(a, b)
    elif isinstance(num_factory, num.FloatingNumberFactory):
        return elements_floating.mul(a, b)
    else:
        raise NotImplementedError('Unknown numeric number typ used.')


def add(a, b):
    """
    Pipeline node which adds the two given parameters.
    Optimization is performed where possible.
    The return type is int if both parameters were integer and so the result is static.
    Otherwise a SeqNode is returned.
    :param a: parameter a
    :param b: parameter b
    :return: int or pipeline node
    """
    num_factory = num.get_numeric_factory()

    if isinstance(num_factory, num.SignedFixedNumberFactory):
        return elements_fixed.add(a, b)
    elif isinstance(num_factory, num.FloatingNumberFactory):
        return elements_floating.add(a, b)
    else:
        raise NotImplementedError('Unknown numeric number typ used.')


def sub(a, b):
    """
    Pipeline node which substracts b from a.
    Optimization is performed where possible.
    The return type is int if both parameters were integer and so the result is static.
    Otherwise a SeqNode is returned.
    :param a: parameter a
    :param b: parameter b
    :return: int or pipeline node
    """
    num_factory = num.get_numeric_factory()

    if isinstance(num_factory, num.SignedFixedNumberFactory):
        return elements_fixed.sub(a, b)
    elif isinstance(num_factory, num.FloatingNumberFactory):
        return elements_floating.sub(a, b)
    else:
        raise NotImplementedError('Unknown numeric number typ used.')


def negate(val):
    """
    Pipeline node which negates the given parameter.
    The return type is int if the type of the parameter is also int.
    Otherwise a SeqNode is returned.
    :param val: parameter val
    :return: int or pipeline node
    """
    num_factory = num.get_numeric_factory()

    if isinstance(num_factory, num.SignedFixedNumberFactory):
        return elements_fixed.negate(val)
    elif isinstance(num_factory, num.FloatingNumberFactory):
        return elements_floating.negate(val)
    else:
        raise NotImplementedError('Unknown numeric number typ used.')
