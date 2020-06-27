from myhdl import SignalType

from generator.pipeline_elements import add, mul


class UnequalVectorLength(Exception):
    pass


def reduce_sum(vec):
    if len(vec) == 0:
        return 0
    elif len(vec) == 1:
        return vec[0]
    else:
        res_vec = vec.copy()
        while len(res_vec) >= 2:
            in_vec = res_vec
            res_vec = []
            while len(in_vec) >= 2:
                res_vec.append(
                    add(in_vec.pop(), in_vec.pop())
                )
            if len(in_vec) == 1:
                res_vec.append(in_vec[0])
        return res_vec[0]


def vec_mul(vec_a, vec_b):
    if len(vec_a) != len(vec_b):
        raise UnequalVectorLength("len(in_a) = %d != len(in_b) = %d" % (len(vec_a), len(vec_b)))
    n_elements = len(vec_a)

    # Remove elements where one factor is 0
    valid = [
        (isinstance(vec_a[i], SignalType) or vec_a[i] != 0)
        and (isinstance(vec_b[i], SignalType) or vec_b[i] != 0)
        for i in range(n_elements)
    ]
    vec_a = [vec_a[i] for i in range(n_elements) if valid[i]]
    vec_b = [vec_b[i] for i in range(n_elements) if valid[i]]
    n_elements = len(vec_a)

    if n_elements == 0:
        return 0
    elif n_elements == 1:
        return mul(vec_a[0], vec_b[0])
    else:
        partial_results = []
        for i in range(n_elements):
            partial_results.append(mul(vec_a[i], vec_b[i]))
        return reduce_sum(partial_results)
