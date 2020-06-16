from typing import Union

from myhdl import intbv, Signal, block, always_seq, instances

from generator.pipeline import InnerNode, Pipe, PipeInput, PipeOutput, PipeSignal
from generator.utils import clone_signal
from utils import num


class Mul(InnerNode):
    def __init__(self, a, b):
        super().__init__()

        self.add_input(a=a, b=b)
        res = Signal(num.default())
        self.add_output(res)

        @block
        def logic(clk, stage, node_input, node_output):
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
        self.logic = logic


class Add(InnerNode):
    def __init__(self, a, b):
        super().__init__()

        self.add_input(a=a, b=b)
        res = Signal(num.default())
        self.add_output(res)

        @block
        def logic(clk, stage, node_input, node_output):
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
        self.logic = logic


def negate(value: Union[PipeSignal, int]) -> Union[PipeSignal, int]:
    if isinstance(value, int):
        return -value

    node = InnerNode()

    node.add_producer(value.producer)
    res = clone_signal(value.signal)
    return PipeSignal(signal=res, producer=node)


def test():
    data1_raw = Signal(intbv(0)[32:])
    input_valid = Signal(bool(0))
    output_busy = Signal(bool(0))

    pipe_in = PipeInput(input_valid, a=data1_raw)
    add1 = Add(pipe_in.a, 3)
    add2 = Add(add1, 3)
    mul1 = Mul(add1, 5)
    mul2 = Mul(add2, pipe_in.a)
    pipe_out = PipeOutput(output_busy, a=mul1, b=mul2)

    return Pipe(pipe_in, pipe_out)


if __name__ == '__main__':
    test()
