from myhdl import block, always_seq, instances, Signal
from pyparsing import *

import num


def get_expr_grammar():
    decimal = Regex(r"\d([\d ])*(\.\d*)?")
    decimal.setParseAction(lambda t: float(t[0].replace(" ", "")))
    # TODO change grammar to allow generic variables, optional lists
    variable = Group(Word("xy", exact=1).setResultsName("var") + Literal("[")
                     + Word(nums).setParseAction(lambda t: int(t[0])).setResultsName("index") + Literal("]"))
    operand = decimal | variable

    # expop = Literal("^")
    signop = oneOf("+ -")
    multop = oneOf("*")
    plusop = oneOf("+ -")

    grammar = infixNotation(
        operand,
        [
            (signop('sign'), 1, opAssoc.RIGHT),
            (multop('op'), 2, opAssoc.LEFT),
            (plusop('op'), 2, opAssoc.LEFT),
        ],
    )
    return grammar


@block
def expr(expression, scope, result, clk=None):
    def generate_logic(parse_tree):
        if isinstance(parse_tree, ParseResults):
            if 'index' in parse_tree and 'var' in parse_tree:
                if parse_tree['var'] in scope:
                    return [], scope[parse_tree['var']][parse_tree['index']]
                else:
                    raise Exception('Unknown var identifier found: %s' % parse_tree['var'])
            elif 'sign' in parse_tree and len(parse_tree) == 2:
                if parse_tree['sign'] == '+':
                    return generate_logic(parse_tree[1])
                elif parse_tree['sign'] == '-':
                    val = Signal(num.same_as(result))
                    rhs = generate_logic(parse_tree[1])
                    zero = Signal(num.from_float(0, sig=rhs[1]))
                    add_inst = num.sub(zero, rhs[1], val)
                    return rhs[0] + [add_inst], val
                else:
                    raise Exception('Unhandled sign operator found: %s' % parse_tree['sign'])
            elif 'op' in parse_tree and len(parse_tree) == 3:
                if parse_tree['op'] == '+':
                    mod = num.add
                elif parse_tree['op'] == '-':
                    mod = num.sub
                elif parse_tree['op'] == '*':
                    mod = num.mul
                else:
                    raise Exception('Unhandled operator found: %s' % parse_tree['op'])
                val = Signal(num.same_as(result))
                lhs = generate_logic(parse_tree[0])
                rhs = generate_logic(parse_tree[2])
                inst = mod(lhs[1], rhs[1], val)
                return lhs[0] + rhs[0] + [inst], val
        elif isinstance(parse_tree, float):
            return [], Signal(num.from_float(parse_tree, result))
        raise Exception('Unknown Parse Error')

    res = get_expr_grammar().parseString(expression, parseAll=True)
    # TODO handle prop_delay, maybe enable finish implementation
    (insts, out, prop_delay) = generate_logic(res[0])

    @always_seq(clk.posedge, reset=None)
    def calc():
        result.next = out

    return instances()
