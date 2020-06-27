from generator.pipeline_elements import add, mul
from generator.vector_utils import UnequalVectorLength, vec_mul, reduce_sum
from generator.tests.helper import PipeTestCase
from utils import num


class TestVectorUtils(PipeTestCase):
    def test_vec_mul_unequal_vector_len(self):
        """Check if exception is raised if vec length is unequal."""
        def inner_pipe(data):
            res = vec_mul([data], [num.int_from_float(2), num.int_from_float(3)])
            return res

        with self.assertRaises(UnequalVectorLength):
            self.run_pipe(inner_pipe, list(range(40)), list(range(40)))

    def test_vec_mul_no_element(self):
        """Check if vector of length 0 is working."""
        def inner_pipe(data):
            vec_res = vec_mul([], [])
            val = add(data, vec_res)
            res = add(val, num.int_from_float(1))
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i + 1 for i in range(40)])

    def test_vec_mul_one_element(self):
        """Check if vector of length 1 is working."""
        def inner_pipe(data):
            res = vec_mul([data], [num.int_from_float(2)])
            return res

        self.run_pipe(inner_pipe, list(range(40)), [2 * i for i in range(40)])

    def test_vec_mul(self):
        """Check if longer vectors are working."""
        def inner_pipe(data):
            add1 = add(data, num.int_from_float(5))
            mul1 = mul(num.int_from_float(2), data)
            mul2 = mul(add1, data)
            res = vec_mul(
                [
                    data,
                    mul1,
                    add1,
                    mul2,
                    num.int_from_float(1)],
                [
                    num.int_from_float(2),
                    num.int_from_float(1),
                    num.int_from_float(0.5),
                    num.int_from_float(5),
                    num.int_from_float(2),
                ]
            )
            return res

        self.run_pipe(inner_pipe,
                      list(range(40)),
                      [
                          2 * i
                          + 2 * i
                          + (i + 5) * 0.5
                          + (i + 5) * i * 5
                          + 1 * 2 for i in range(40)
                      ])

    def test_reduce_sum_even(self):
        """
        Testing the reduce_sum pipeline element.
        """

        def inner_pipe(data):
            res = reduce_sum([data for _ in range(4)])
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i * 4 for i in range(40)])

    def test_reduce_sum_odd(self):
        """
        Testing the reduce_sum pipeline element.
        """

        def inner_pipe(data):
            res = reduce_sum([data for _ in range(5)])
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i * 5 for i in range(40)])

    def test_reduce_sum_len1(self):
        """
        Testing the reduce_sum pipeline element with len 1.
        """

        def inner_pipe(data):
            val = reduce_sum([data])
            res = add(val, num.int_from_float(1))
            return res

        self.run_pipe(inner_pipe, list(range(40)), [i + 1 for i in range(40)])
