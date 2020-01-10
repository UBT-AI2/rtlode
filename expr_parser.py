from myhdl import block, always_seq, Signal, always_comb
from pyparsing import *

import num


class ExprParserException(Exception):
    pass


def get_expr_grammar():
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


@block
def expr(expression, scope, result, clk=None):
    @block
    def generate_logic(parse_tree, out):
        if isinstance(parse_tree, ParseResults):
            if 'var' in parse_tree:
                if parse_tree['var'] in scope:
                    if 'index' in parse_tree:
                        var = scope[parse_tree['var']][parse_tree['index']]
                    else:
                        var = scope[parse_tree['var']]

                    @always_comb
                    def assign():
                        out.next = var

                    return [assign]
                else:
                    raise ExprParserException('Unknown var identifier found: %s' % parse_tree['var'])
            elif 'sign' in parse_tree and len(parse_tree) == 2:
                if parse_tree['sign'] == '+':
                    return generate_logic(parse_tree[1], out)
                elif parse_tree['sign'] == '-':
                    val = Signal(num.same_as(result))
                    rhs = generate_logic(parse_tree[1], val)
                    zero = Signal(num.from_float(0, sig=val))
                    inst = num.sub(zero, val, out)
                    return [rhs] + [inst]
                else:
                    raise ExprParserException('Unhandled sign operator found: %s' % parse_tree['sign'])
            elif 'op' in parse_tree and len(parse_tree) == 3:
                if parse_tree['op'] == '+':
                    mod = num.add
                elif parse_tree['op'] == '-':
                    mod = num.sub
                elif parse_tree['op'] == '*':
                    mod = num.mul
                else:
                    raise ExprParserException('Unhandled operator found: %s' % parse_tree['op'])
                val_lhs = Signal(num.same_as(result))
                val_rhs = Signal(num.same_as(result))
                lhs = generate_logic(parse_tree[0], val_lhs)
                rhs = generate_logic(parse_tree[2], val_rhs)
                inst = mod(val_lhs, val_rhs, out)
                return [lhs] + [rhs] + [inst]
        elif isinstance(parse_tree, float):
            const = Signal(num.from_float(parse_tree, result))

            @always_comb
            def assign():
                out.next = const

            return [assign]
        raise ExprParserException('Unknown Parse Error')

    res = get_expr_grammar().parseString(expression, parseAll=True)
    # TODO handle prop_delay, maybe enable finish implementation
    expr_out = Signal(num.same_as(result))
    insts = generate_logic(res[0], expr_out)

    @always_seq(clk.posedge, reset=None)
    def calc():
        result.next = expr_out

    return [insts, calc]
