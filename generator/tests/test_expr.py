from generator.expr_parser import expr
from generator.tests.helper import PipeTestCase
from utils import num


class TestExpr(PipeTestCase):
    testset = [
        ('multiple sign ops', '--+-x', lambda x: -x),
        ('add op with decimal', 'x+3.15', lambda x: x + 3.15),
        ('parenthese', '(x+1)', lambda x: x+1),
        ('multiple parenthese', '(((x+1)))', lambda x: x+1),
        ('sign op with var', '-x', lambda x: -x),
        ('add op with var', '2+x', lambda x: 2+x),
        ('sub op with var', '2-x', lambda x: 2-x),
        ('mul op with var', '2*x', lambda x: 2*x),
        ('mul ops of same hierarchy', 'x*x*x', lambda x: x*x*x),
        ('add and sub ops of same hierarchy', 'x+2-x', lambda x: x+2-x),
        ('mul add priorization', '3+2*x', lambda x: 3+2*x),
        ('parenthese priorization', '(3+2)*x', lambda x: (3+2)*x),
    ]

    def test_expr(self):
        """Checking whole testset with different aspects."""

        for test in self.testset:

            (desc, expr_str, res_lambda) = test
            print("Expr: %s" % expr_str)

            def convert_scope(data):
                if isinstance(data, int) or isinstance(data, float):
                    return num.from_float(data)
                elif isinstance(data, list):
                    return list(map(convert_scope, data))
                elif isinstance(data, dict):
                    res_data = {}
                    for var in data:
                        res_data[var] = convert_scope(data[var])
                    return res_data
                raise Exception('Can\'t convert data chunk to signals.')

            def inner_pipe(data):
                res = expr(expr_str, {'x': data})
                return res

            self.run_pipe(inner_pipe, list(range(40)), [res_lambda(i) for i in range(40)])
