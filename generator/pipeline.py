from __future__ import annotations

from typing import List, Set, Dict

from myhdl import SignalType, Signal, block, instances, always_seq

from generator.utils import clone_signal

"""
Pipeline Utility

This file provides all necessary parts to generate a parallized pipeline from a dataflow like description.
An example of a simple pipeline:
```
        in_valid = Signal(bool(0))
        in_signal = Signal(num.default())

        out_busy = Signal(bool(0))

        data_in = PipeInput(in_valid, a=in_signal)
        add1 = add(data_in.a, num.int_from_float(3))
        mul1 = mul(add1, data_in.a)
        data_out = PipeOutput(out_busy, res=mul1)
        myhdl_pipe_instances = Pipe(data_in, data_out).create(clk, rst)
```
The generated pipeline can be driven each clk cycle. The input must provide an boolean valid signal. The output must
be provide a boolean busy signal, and is able to stall the pipeline with this signal. However the output must be able
to process one more value after stalling the output.
"""


class _DynamicInterface:
    """
    Utility to provide a myhdl block with an interface dynamically defined at runtime.
    """
    def __init__(self, **kwargs):
        """
        Returns an object which has attributes at given keys and with given values of kwargs.
        The type of the values is restricted to: _PipeSignal, ProducerNode, SignalType, int
        :param kwargs: description of which attributes should have which values
        """
        for key, value in kwargs.items():
            try:
                value = value.get_signal()
            except AttributeError:
                pass
            if not isinstance(value, SignalType) and not isinstance(value, int):
                raise NotImplementedError()
            setattr(self, key, value)


class _PipeSignal:
    """
    An internal signal of the pipe. Containing the signal itself but also the producers of the signal.
    """
    signal: SignalType
    producer: ProducerNode

    def __init__(self, signal: SignalType, producer: ProducerNode):
        self.signal = signal
        self.producer = producer

    def get_producer(self):
        return self.producer

    def get_signal(self):
        return self.signal


class NoSeqNodeError(Exception):
    pass


class Pipe:
    pipe_input: PipeInput
    pipe_output: PipeOutput
    comb_logic: List
    stages: List[Stage]

    def __init__(self, producer: PipeInput, consumer: PipeOutput):
        self.pipe_input = producer
        self.pipe_output = consumer
        self.comb_logic = []

    def get_stats(self):
        self.resolve()
        stats = {
            'nbr_nodes': 0,
            'nbr_seq_nodes': 0,
            'nbr_comb_nodes': 0,
            'nbr_regs': 0,
            'nbr_stages': len(self.stages),
            'by_type': {}
        }
        already_visited = [self.pipe_output]
        to_visit = self.pipe_output.get_producers()
        while len(to_visit) > 0:
            p = to_visit.pop()
            if p not in already_visited:
                if isinstance(p, _Node):
                    stats['nbr_nodes'] += 1
                    if p.name in stats['by_type']:
                        stats['by_type'][p.name] += 1
                    else:
                        stats['by_type'][p.name] = 1
                if isinstance(p, SeqNode):
                    stats['nbr_seq_nodes'] += 1
                elif isinstance(p, CombNode):
                    stats['nbr_comb_nodes'] += 1

                if isinstance(p, Register):
                    stats['nbr_regs'] += 1

                already_visited.append(p)
                if isinstance(p, ConsumerNode):
                    to_visit.update(p.get_producers())
        return stats

    def add_to_stage(self, node: _Node):
        assert node.stage_index is not None

        if len(self.stages) <= node.stage_index:
            self.stages.append(Stage())
        self.stages[node.stage_index].add(node)

    def resolve(self):
        # TODO recognize circles and abort
        self.stages = []

        to_visit = self.pipe_input.get_consumers()
        while len(to_visit) > 0:
            node = to_visit.pop()
            if isinstance(node, PipeInput):
                assert self.pipe_input == node
                continue
            elif isinstance(node, PipeOutput):
                assert self.pipe_output == node
                continue
            elif not isinstance(node, _Node):
                raise NotImplementedError()

            stage = 0
            for p in node.get_producers():
                lowest_possible_stage = None
                if isinstance(p, PipeInput):
                    lowest_possible_stage = 0
                elif isinstance(p, SeqNode):
                    if p.stage_index is not None:
                        lowest_possible_stage = p.stage_index + 1
                elif isinstance(p, CombNode):
                    lowest_possible_stage = p.stage_index
                if lowest_possible_stage is None:
                    stage = None
                elif stage is not None:
                    stage = max(stage, lowest_possible_stage)
            if stage is not None:
                node.stage_index = stage
                self.add_to_stage(node)
                if isinstance(node, ProducerNode):
                    to_visit.update(node.get_consumers())
                for name in node.get_inputs().keys():
                    try:
                        p = node.get_inputs()[name].get_producer()
                        if isinstance(p, PipeInput):
                            min_reg_stage = 0
                        elif isinstance(p, SeqNode):
                            min_reg_stage = p.stage_index + 1
                        elif isinstance(p, CombNode):
                            min_reg_stage = p.stage_index
                        else:
                            raise NotImplementedError()
                        for reg_stage in range(min_reg_stage, node.stage_index):
                            value = node.get_inputs()[name]
                            reg = Register(value)
                            reg.stage_index = reg_stage
                            self.add_to_stage(reg)
                            node.replace_input(**{name: reg})
                    except AttributeError:
                        continue
            else:
                to_visit.add(node)

        # Check if last stage contains only CombLogic
        for node in self.stages[-1].nodes:
            if not isinstance(node, CombNode):
                break
        else:
            # Migrate all nodes to one stage earlier
            if len(self.stages) < 2:
                raise NoSeqNodeError('At least one SeqNode is required in a pipeline.')
            self.stages[-2].nodes.update(self.stages[-1].nodes)
            del self.stages[-1]

        return self.stages

    @block
    def create(self, clk, rst):
        self.resolve()
        stage_instances = []

        for stage_id, stage in enumerate(self.stages):
            if stage_id == 0:
                # First stage after Input
                previous_valid = self.pipe_input.valid
                self.pipe_input.set_pipe_busy(stage.busy)
            else:
                previous_valid = self.stages[stage_id - 1].valid

            if stage_id == len(self.stages) - 1:
                # Last stage before Output
                next_busy = self.pipe_output.busy
                self.pipe_output.set_pipe_valid(stage.valid)
            else:
                next_busy = self.stages[stage_id + 1].busy

            stage_instances.append(
                stage_logic(clk, rst, stage, previous_valid, next_busy)
            )
            for node in stage.nodes:
                node_input = _DynamicInterface(**node.get_inputs())
                node_output = _DynamicInterface(**node.get_outputs())
                if isinstance(node, SeqNode):
                    instance = node.logic(clk, stage, node_input, node_output)
                elif isinstance(node, CombNode):
                    instance = node.logic(node_input, node_output)
                else:
                    raise NotImplementedError()
                stage_instances.append(instance)

        return stage_instances


class ProducerNode:
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
            signal = self._output_signals[name]
            if isinstance(signal, list):
                return list(
                    map(
                        lambda x: _PipeSignal(signal=x, producer=self),
                        signal
                    ))
            else:
                return _PipeSignal(signal=signal, producer=self)
        raise AttributeError()

    # Be compatible to Pipe Signal
    def get_producer(self):
        return self

    def get_signal(self):
        return self._output_signals['default']


class ConsumerNode:
    _inputs: Dict

    def __init__(self):
        super().__init__()
        self._inputs = {}

    def add_input(self, **kwargs):
        for name, in_arg in kwargs.items():
            if name in self._inputs:
                self.replace_input(**kwargs)
            else:
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
            # Deregister for old producers
            try:
                p = old_in.get_producer()
                p.deregister_consumer(self)
            except AttributeError:
                pass
            # Register for new producers
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


class _Node(ProducerNode, ConsumerNode):
    """
    An inner element of the pipeline.
    Should not be used directly, use SeqNode or CombNode.
    """
    def __init__(self):
        super().__init__()

        self.logic = None
        self.stage_index = None
        self.name = 'N/A'

    def set_logic(self, logic):
        self.logic = logic

    def get_logic(self):
        return self.logic

    def set_name(self, name):
        self.name = name


class SeqNode(_Node):
    """
    A sequential node of the pipeline. The nodes logic must take exactly one clk cycle.

    The provided logic must be of the following function signature:
        def logic(clk, stage, node_input, node_output)
    """
    def __init__(self):
        super().__init__()


class CombNode(_Node):
    """
    A combinatorical node of the pipeline. The logic must use only combinational logic.
    The complexety must be minimized. Intendet for low/no cost logic like shifting of signals.

    The provided logic must be of the following function signature:
        def logic(node_input, node_output)
    """
    def __init__(self):
        super().__init__()


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
            signal = self._inputs[name]
            if isinstance(signal, list):
                return list(
                    map(
                        lambda x: x.get_signal(),
                        signal
                    ))
            else:
                return signal.get_signal()
        raise AttributeError()

    def set_pipe_valid(self, valid_signal):
        self.pipe_valid = valid_signal


class Register(SeqNode):
    def __init__(self, val):
        super().__init__()

        if isinstance(val, int):
            raise NotImplementedError()

        self.add_input(default=val)
        res = clone_signal(val.get_signal())
        self.add_output(res)
        self.set_name('reg')

        self.logic = register


@block
def register(clk, stage, node_input, node_output):
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


class Stage:
    busy: SignalType
    valid: SignalType
    data2out: SignalType
    reg2out: SignalType
    data2reg: SignalType
    nodes: Set[SeqNode]

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
