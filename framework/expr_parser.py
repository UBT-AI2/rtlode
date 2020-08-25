import typing

from pyparsing import *

from framework.pipeline import PipeConstant
from framework.pipeline_elements import add, sub, mul, negate


class ExprParserException(Exception):
    pass


def get_expr_grammar():
    """
    Defines the grammar used by the expression parser.

    :return: expr grammar
    """
    decimal = Regex(r"\d([\d ])*(\.\d*)?")
    decimal.setParseAction(lambda t: float(t[0].replace(" ", "")))
    variable = Group(Word(alphas).setResultsName("var") + Optional(Literal("[")
                     + Word(nums).setParseAction(lambda t: int(t[0])).setResultsName("index") + Literal("]")))
    operand = decimal | variable

    signop = oneOf("+ -")
    multop = Literal("*")
    addop = Literal("+")
    subop = Literal("-")

    grammar = infixNotation(
        operand,
        [
            (signop('sign'), 1, opAssoc.RIGHT),
            (multop('op'), 2, opAssoc.LEFT),
            (addop('op'), 2, opAssoc.LEFT),
            (subop('op'), 2, opAssoc.LEFT),
        ],
    )
    return grammar


def _generate_logic(parse_tree, scope):
    if isinstance(parse_tree, ParseResults):
        if 'var' in parse_tree:
            if parse_tree['var'] in scope:
                if 'index' in parse_tree:
                    var = scope[parse_tree['var']][parse_tree['index']]
                else:
                    var = scope[parse_tree['var']]
                return var
            else:
                raise ExprParserException('Unknown var identifier found: %s' % parse_tree['var'])
        elif 'sign' in parse_tree and len(parse_tree) == 2:
            if parse_tree['sign'] == '+':
                return _generate_logic(parse_tree[1], scope)
            elif parse_tree['sign'] == '-':
                return negate(_generate_logic(parse_tree[1], scope))
            else:
                raise ExprParserException('Unhandled sign operator found: %s' % parse_tree['sign'])
        elif 'op' in parse_tree and len(parse_tree) >= 3:
            if parse_tree['op'] == '+':
                mod = add
            elif parse_tree['op'] == '-':
                mod = sub
            elif parse_tree['op'] == '*':
                mod = mul
            else:
                raise ExprParserException('Unhandled operator found: %s' % parse_tree['op'])
            lhs = _generate_logic(parse_tree.pop(0), scope)
            if parse_tree[0] == parse_tree['op']:
                parse_tree.pop(0)
            else:
                raise ExprParserException('Expected operator: %s found: %s' % (parse_tree['op'], parse_tree[0]))
            if len(parse_tree) > 1:
                rhs = _generate_logic(parse_tree, scope)
            else:
                rhs = _generate_logic(parse_tree[0], scope)
            return mod(lhs, rhs)
    elif isinstance(parse_tree, float):
        return PipeConstant.from_float(parse_tree)
    raise ExprParserException('Unknown Parse Error')


def expr(expression: str, scope: typing.Dict):
    """
    Computes the given expression. Variable access to vars provided in
    scpope is provided.

    :param expression: string of expression
    :param scope: dict with var names mapped to vars
    :return: myhdl instances
    """
    res = get_expr_grammar().parseString(expression, parseAll=True)

    return _generate_logic(res[0], scope)
