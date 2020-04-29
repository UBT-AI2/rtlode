import typing

from myhdl import block, always_seq, Signal, always_comb, SignalType
from pyparsing import *

import generator.calc
from utils import num
from generator.utils import clone_signal
from generator.flow import FlowControl
from generator.vector_utils.reduce import reduce_and


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


@block
def expr(expression: str,
         scope: typing.Dict[str, typing.Union[SignalType, typing.List[SignalType]]],
         result: SignalType,
         flow: FlowControl):
    """
    Computes the given expression. Variable access to vars provided in
    scpope is provided.

    :param expression: string of expression
    :param scope: dict with var names mapped to vars
    :param result: result of the expression
    :param flow: FlowControl sigs
    :return: myhdl instances
    """
    @block
    def generate_logic(parse_tree, out: SignalType, expr_flow: FlowControl):
        if isinstance(parse_tree, ParseResults):
            if 'var' in parse_tree:
                if parse_tree['var'] in scope:
                    if 'index' in parse_tree:
                        var = scope[parse_tree['var']][parse_tree['index']]
                    else:
                        var = scope[parse_tree['var']]

                    @always_seq(expr_flow.clk_edge(), expr_flow.rst)
                    def assign_comb():
                        out.next = var
                        expr_flow.fin.next = True

                    @always_seq(expr_flow.clk_edge(), expr_flow.rst)
                    def assign_seq():
                        if expr_flow.enb:
                            out.next = var
                            expr_flow.fin.next = True

                    if isinstance(var, SignalType):
                        return [assign_seq]
                    else:
                        return [assign_comb]
                else:
                    raise ExprParserException('Unknown var identifier found: %s' % parse_tree['var'])
            elif 'sign' in parse_tree and len(parse_tree) == 2:
                if parse_tree['sign'] == '+':
                    return generate_logic(parse_tree[1], out, expr_flow)
                elif parse_tree['sign'] == '-':
                    val = clone_signal(result)
                    zero = num.signal_from_float(0, sig=val)

                    subflow = expr_flow.create_subflow(enb=expr_flow.enb)
                    rhs = generate_logic(parse_tree[1], val, subflow)
                    inst = generator.calc.sub(zero, val, out, expr_flow.create_subflow(enb=subflow.fin, fin=expr_flow.fin))
                    return [rhs] + [inst]
                else:
                    raise ExprParserException('Unhandled sign operator found: %s' % parse_tree['sign'])
            elif 'op' in parse_tree and len(parse_tree) >= 3:
                if parse_tree['op'] == '+':
                    mod = generator.calc.add
                elif parse_tree['op'] == '-':
                    mod = generator.calc.sub
                elif parse_tree['op'] == '*':
                    mod = generator.calc.mul
                else:
                    raise ExprParserException('Unhandled operator found: %s' % parse_tree['op'])
                val_lhs = clone_signal(result)
                val_rhs = clone_signal(result)
                subflow_lhs = expr_flow.create_subflow(enb=expr_flow.enb)
                subflow_rhs = expr_flow.create_subflow(enb=expr_flow.enb)
                lhs = generate_logic(parse_tree.pop(0), val_lhs, subflow_lhs)
                if parse_tree[0] == parse_tree['op']:
                    parse_tree.pop(0)
                else:
                    raise ExprParserException('Expected operator: %s found: %s' % (parse_tree['op'], parse_tree[0]))
                if len(parse_tree) > 1:
                    rhs = generate_logic(parse_tree, val_rhs, subflow_rhs)
                else:
                    rhs = generate_logic(parse_tree[0], val_rhs, subflow_rhs)
                subflows_finished = clone_signal(expr_flow.fin)
                fin_reduce = reduce_and([subflow_lhs.fin, subflow_rhs.fin], subflows_finished)
                inst = mod(val_lhs, val_rhs, out, expr_flow.create_subflow(enb=subflows_finished, fin=expr_flow.fin))
                return [lhs] + [rhs] + [fin_reduce] + [inst]
        elif isinstance(parse_tree, float):
            const = num.from_float(parse_tree)

            @always_seq(expr_flow.clk_edge(), expr_flow.rst)
            def assign():
                out.next = const
                expr_flow.fin.next = True

            return [assign]
        raise ExprParserException('Unknown Parse Error')

    res = get_expr_grammar().parseString(expression, parseAll=True)
    expr_out = clone_signal(result)
    expr_subflow = flow.create_subflow(enb=flow.enb)
    insts = generate_logic(res[0], expr_out, expr_subflow)

    @always_seq(flow.clk_edge(), reset=flow.rst)
    def calc():
        if expr_subflow.fin:
            result.next = expr_out
            flow.fin.next = True

    return [insts, calc]
