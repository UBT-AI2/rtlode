from myhdl import Signal, block, always_seq, instances

from generator.pipeline import InnerNode
from generator.utils import clone_signal
from utils import num


def mul(a, b):
    node = InnerNode()

    node.add_input(a=a, b=b)
    res = Signal(num.default())
    node.add_output(res)

    @block
    def mul(clk, stage, node_input, node_output):
        reg_data = clone_signal(node_output.default)

        @always_seq(clk.posedge, reset=None)
        def drive_data():
            if stage.data2out:
                node_output.default.next = node_input.a * node_input.b
            if stage.reg2out:
                node_output.default.next = reg_data
            if stage.data2reg:
                reg_data.next = node_input.a * node_input.b
        return instances()
    node.logic = mul
    return node


def add(a, b):
    node = InnerNode()

    node.add_input(a=a, b=b)
    res = Signal(num.default())
    node.add_output(res)

    @block
    def add(clk, stage, node_input, node_output):
        reg_data = clone_signal(node_output.default)

        @always_seq(clk.posedge, reset=None)
        def drive_data():
            if stage.data2out:
                node_output.default.next = node_input.a + node_input.b
            if stage.reg2out:
                node_output.default.next = reg_data
            if stage.data2reg:
                reg_data.next = node_input.a + node_input.b
        return instances()
    node.logic = add
    return node


def sub(a, b):
    node = InnerNode()

    node.add_input(a=a, b=b)
    res = Signal(num.default())
    node.add_output(res)

    @block
    def sub(clk, stage, node_input, node_output):
        reg_data = clone_signal(node_output.default)

        @always_seq(clk.posedge, reset=None)
        def drive_data():
            if stage.data2out:
                node_output.default.next = node_input.a - node_input.b
            if stage.reg2out:
                node_output.default.next = reg_data
            if stage.data2reg:
                reg_data.next = node_input.a - node_input.b
        return instances()
    node.logic = sub
    return node
