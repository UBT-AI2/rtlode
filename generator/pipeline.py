from __future__ import annotations

from typing import List, Set, Dict

from myhdl import SignalType, Signal, block, instances, always_seq

from generator.utils import clone_signal


class DynamicInterface:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            try:
                value = value.get_signal()
            except AttributeError:
                pass
            if not isinstance(value, SignalType) and not isinstance(value, int):
                raise NotImplementedError()
            setattr(self, key, value)


class PipeSignal:
    signal: SignalType
    producer: ProducerNode

    def __init__(self, signal: SignalType, producer: ProducerNode):
        self.signal = signal
        self.producer = producer

    def get_producer(self):
        return self.producer

    def get_signal(self):
        return self.signal


class Pipe:
    pipe_input: PipeInput
    pipe_output: PipeOutput
    stages: List[Stage]

    def __init__(self, producer: PipeInput, consumer: PipeOutput):
        self.pipe_input = producer
        self.pipe_output = consumer
        self.pipe_output.stage_index = 0

    def get_stats(self):
        already_visited = [self.pipe_output]
        to_visit = self.pipe_output.get_producers()
        while len(to_visit) > 0:
            p = to_visit.pop()
            if p not in already_visited:
                already_visited.append(p)
                if isinstance(p, ConsumerNode):
                    to_visit.update(p.get_producers())
        return len(already_visited)

    def resolve(self):
        # TODO recognize circles and abort
        # TODO check that only one producer present
        self.stages = []
        current_stage = 1
        candidates_next_stage = set(self.pipe_output.get_producers())

        while len(candidates_next_stage) > 0:
            # Break
            stage = Stage()
            candidates_stage = candidates_next_stage
            candidates_next_stage = set()
            for node in candidates_stage:
                if isinstance(node, PipeInput):
                    assert node == self.pipe_input

                if all(c.stage_index is not None and c.stage_index == current_stage - 1
                       for c in node.get_consumers()):
                    node.stage_index = current_stage
                    if not isinstance(node, PipeInput):
                        stage.add(node)
                    if isinstance(node, ConsumerNode):
                        candidates_next_stage.update(node.get_producers())
                else:
                    # Not all consumer in previous stage
                    for c in node.get_consumers():
                        if c.stage_index is not None and c.stage_index < current_stage:
                            # Add register to fill empty stages
                            for name, in_arg in c.get_inputs().items():
                                try:
                                    p = in_arg.get_producer()
                                    if p == node:
                                        # This input must be buffered by a register
                                        reg = Register(in_arg)
                                        reg.stage_index = current_stage
                                        stage.add(reg)
                                        c.replace_input(**{name: reg})
                                except AttributeError as e:
                                    continue

                    candidates_next_stage.add(node)

            if len(stage) > 0:
                self.stages.append(stage)
                current_stage += 1

        return self.stages

    @block
    def create(self, clk, rst):
        self.resolve()
        stage_instances = []

        for stage_id, stage in enumerate(self.stages):
            if stage_id == 0:
                # First stage before Consumer
                next_busy = self.pipe_output.busy
                self.pipe_output.set_pipe_valid(stage.valid)
            else:
                next_busy = self.stages[stage_id - 1].busy

            if stage_id == len(self.stages) - 1:
                # Last stage before Producer
                previous_valid = self.pipe_input.valid
                self.pipe_input.set_pipe_busy(stage.busy)
            else:
                previous_valid = self.stages[stage_id + 1].valid

            stage_instances.append(
                stage_logic(clk, rst, stage, previous_valid, next_busy)
            )
            for node in stage.nodes:
                node_input = DynamicInterface(**node.get_inputs())
                node_output = DynamicInterface(**node.get_outputs())
                stage_instances.append(
                    node.logic(clk, stage, node_input, node_output)
                )

        return stage_instances


class Node:
    stage_index: int

    def __init__(self):
        self.stage_index = None


class ProducerNode(Node):
    _consumer_nodes: Set[ConsumerNode]
    _output_signals: Dict

    def __init__(self):
        super().__init__()
        self._consumer_nodes = set()
        self._output_signals = {}

    def add_output(self, default=None, **kwargs):
        if default is not None:
            self._output_signals['default'] = default

        self._output_signals.update(kwargs)

    def register_consumer(self, consumer: ConsumerNode):
        self._consumer_nodes.add(consumer)

    def deregister_consumer(self, consumer):
        self._consumer_nodes.remove(consumer)

    def get_consumers(self):
        return self._consumer_nodes.copy()

    def get_outputs(self):
        return self._output_signals

    def __getattr__(self, name):
        if name in self._output_signals:
            return PipeSignal(signal=self._output_signals[name], producer=self)
        raise AttributeError()

    # Be compatible to Pipe Signal
    def get_producer(self):
        return self

    def get_signal(self):
        return self._output_signals['default']


class ConsumerNode(Node):
    _inputs: Dict

    def __init__(self):
        super().__init__()
        self._inputs = {}

    def add_input(self, **kwargs):
        for name, in_arg in kwargs.items():
            try:
                p = in_arg.get_producer()
                p.register_consumer(self)
            except AttributeError:
                pass
            self._inputs[name] = in_arg

    def get_inputs(self):
        return self._inputs

    def replace_input(self, **kwargs):
        for name, new_in in kwargs.items():
            assert name in self._inputs
            old_in = self._inputs[name]
            # Deregister for old producer
            try:
                p = old_in.get_producer()
                p.deregister_consumer(self)
            except AttributeError:
                pass
            # Register for new producer
            try:
                p = new_in.get_producer()
                p.register_consumer(self)
            except AttributeError:
                pass
            self._inputs[name] = new_in

    def get_producers(self) -> Set:
        producers = set()
        for in_arg in self._inputs.values():
            try:
                p = in_arg.get_producer()
                producers.add(p)
            except AttributeError:
                continue
        return producers


class InnerNode(ProducerNode, ConsumerNode):
    def __init__(self):
        super().__init__()

        self.logic = None

    # logic must be a function of this signature
    # def logic(clk, stage, node_input, node_output):
    #     raise NotImplementedError()


class PipeInput(ProducerNode):
    valid: SignalType
    pipe_busy: SignalType

    def __init__(self, input_valid: SignalType, **raw_signals: SignalType):
        super().__init__()

        self.valid = input_valid
        self.pipe_busy = None

        self.add_output(**raw_signals)

    def set_pipe_busy(self, busy_signal):
        self.pipe_busy = busy_signal


class PipeOutput(ConsumerNode):
    busy: SignalType
    pipe_valid: SignalType

    def __init__(self, busy: SignalType, **inputs):
        super().__init__()

        self.busy = busy
        self.pipe_valid = None

        self.add_input(**inputs)

    def __getattr__(self, name):
        if name in self._inputs:
            return self._inputs[name].get_signal()
        raise AttributeError()

    def set_pipe_valid(self, valid_signal):
        self.pipe_valid = valid_signal


class Stage:
    busy: SignalType
    valid: SignalType
    data2out: SignalType
    reg2out: SignalType
    data2reg: SignalType
    nodes: Set[InnerNode]

    def __init__(self, nodes=None):
        self.busy = Signal(bool(0))
        self.valid = Signal(bool(0))
        self.data2out = Signal(bool(0))
        self.reg2out = Signal(bool(0))
        self.data2reg = Signal(bool(0))
        if nodes is None:
            self.nodes = set()
        else:
            self.nodes = nodes

    def add(self, node):
        self.nodes.add(node)

    def __len__(self):
        return self.nodes.__len__()


@block
def stage_logic(clk, rst, stage, in_valid, out_busy):
    @always_seq(clk.posedge, reset=None)
    def control():
        stage.data2out.next = False
        stage.reg2out.next = False
        stage.data2reg.next = False
        if rst:
            stage.busy.next = False
            stage.valid.next = False
        elif not out_busy:
            # Next stage not busy
            if not stage.busy:
                # Buffer empty
                stage.valid.next = in_valid
                stage.data2out.next = True
            else:
                # Push buffer data out
                stage.valid.next = True
                stage.reg2out.next = True

            # Consumer not busy
            stage.busy.next = False
        elif not stage.valid:
            # Just pass valid signals
            stage.valid.next = in_valid
            stage.busy.next = False

            stage.data2out.next = True
        elif in_valid and not stage.busy:
            stage.busy.next = in_valid and stage.valid

        if not stage.busy:
            stage.data2reg.next = True

    return instances()


class Register(InnerNode):
    def __init__(self, val):
        super().__init__()

        if isinstance(val, int):
            raise NotImplementedError()

        self.add_input(default=val)
        res = clone_signal(val.get_signal())
        self.add_output(res)

        @block
        def logic(clk, stage, node_input, node_output):
            reg_data = clone_signal(node_output.default)

            @always_seq(clk.posedge, reset=None)
            def drive_data():
                if stage.data2out:
                    node_output.default.next = node_input.default
                if stage.reg2out:
                    node_output.default.next = reg_data
                if stage.data2reg:
                    reg_data.next = node_input.default
            return instances()
        self.logic = logic
