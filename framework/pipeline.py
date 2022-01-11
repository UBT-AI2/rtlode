from __future__ import annotations

from typing import List, Set, Dict, Iterable, Optional, Union

from myhdl import SignalType, Signal, block, instances, always_seq, always_comb, ConcatSignal

from framework import packed_struct
from framework.fifo import fifo, FifoProducer, FifoConsumer
from framework.packed_struct import StructDescription, BitVector, PackedReadStruct, PackedWriteStruct
from generator.utils import clone_signal
from utils.num import NumberType

"""
Pipeline Utility

This file provides all necessary parts to generate a parallelized pipeline from a dataflow like description.
An example of a simple pipeline:
```
        in_valid = Signal(bool(0))
        in_signal = Signal(num.get_numeric_factory().create())

        out_busy = Signal(bool(0))

        data_in = PipeInput(in_valid, a=in_signal)
        add1 = add(data_in.a, PipeConstant.from_float(3))
        mul1 = mul(add1, data_in.a)
        data_out = PipeOutput(out_busy, res=mul1)
        myhdl_pipe_instances = Pipe(data_in, data_out).create(clk, rst)
```
The generated pipeline can be driven each clk cycle. The input must provide an boolean valid signal. The output must
be provide a boolean busy signal, and is able to stall the pipeline with this signal. However the output must be able
to process one more value after stalling the output.
"""


def _next_stage(p):
    min_reg_stage = None
    if isinstance(p, PipeInput):
        min_reg_stage = 0
    elif isinstance(p, OneCycleNode):
        if p.stage_index is not None:
            min_reg_stage = p.stage_index + 1
    elif isinstance(p, ZeroCycleNode):
        min_reg_stage = p.stage_index
    elif isinstance(p, MultipleCycleNode):
        if p.stage_index is not None:
            min_reg_stage = p.stage_index + 1
    else:
        raise NotImplementedError()
    return min_reg_stage


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
            try:
                value = value.get_value()
            except AttributeError:
                pass
            if not isinstance(value, SignalType) and not isinstance(value, int):
                raise NotImplementedError()
            setattr(self, key, value)


class _OrderedSet:
    """
    Utility providing the functionality of an ordered set.
    The implementation is based on an internal list with checks on each insertion if the values is already present.
    This is not very performant but sufficient for the purpose.
    """
    def __init__(self, values: Iterable = None):
        self._data = []
        if values is not None:
            self.update(values)

    def update(self, values: Iterable):
        for val in values:
            self.add(val)

    def add(self, value):
        if value not in self._data:
            self._data.append(value)

    def __len__(self):
        return len(self._data)

    def pop(self, index=0):
        return self._data.pop(index)


class PipeNumeric:
    """
    Class overloading the python operators with the pipe base numerical nodes.
    """
    number_type: Optional[NumberType]

    def __init__(self, number_type: NumberType = None):
        super().__init__()
        self.number_type = number_type

    def set_type(self, number_type: NumberType):
        self.number_type = number_type

    def get_type(self):
        return self.number_type

    def __add__(self, other: PipeNumeric):
        if not isinstance(other, PipeNumeric):
            return NotImplemented

        from framework.pipeline_elements import add
        return add(self, other)

    def __radd__(self, other: PipeNumeric):
        if not isinstance(other, PipeNumeric):
            return NotImplemented

        from framework.pipeline_elements import add
        return add(other, self)

    def __sub__(self, other: PipeNumeric):
        if not isinstance(other, PipeNumeric):
            return NotImplemented

        from framework.pipeline_elements import sub
        return sub(self, other)

    def __rsub__(self, other: PipeNumeric):
        if not isinstance(other, PipeNumeric):
            return NotImplemented

        from framework.pipeline_elements import sub
        return sub(other, self)

    def __mul__(self, other: PipeNumeric):
        if not isinstance(other, PipeNumeric):
            return NotImplemented

        from framework.pipeline_elements import mul
        return mul(self, other)

    def __rmul__(self, other: PipeNumeric):
        if not isinstance(other, PipeNumeric):
            return NotImplemented

        from framework.pipeline_elements import mul
        return mul(other, self)


class PipeConstant(PipeNumeric):
    value: int

    def __init__(self, number_type: NumberType, value):
        super().__init__(number_type)
        self.value = value

    def get_value(self):
        return self.value

    @staticmethod
    def from_float(float_val, number_type=None):
        from utils import num
        if number_type is None:
            number_type = num.get_default_type()
        return PipeConstant(number_type, number_type.create_constant(float_val))


class PipeSignal(PipeNumeric):
    """
    An internal signal of the pipe. Containing the signal itself but also the producers of the signal.
    Supporting basic numeric operations by operation overloading.
    """
    signal: Optional[SignalType]
    producer: Optional[ProducerNode]

    def __init__(self, number_type: NumberType = None, signal: SignalType = None, producer: ProducerNode = None):
        super().__init__(number_type)
        self.signal = signal
        self.producer = producer

    def get_producer(self):
        return self.producer

    def set_producer(self, producer):
        self.producer = producer

    def get_signal(self):
        return self.signal

    def set_signal(self, signal):
        self.signal = signal

    def update(self, pipe_signal: PipeSignal):
        self.set_type(pipe_signal.get_type())
        self.set_signal(pipe_signal.get_signal())
        self.set_producer(pipe_signal.get_producer())


class Pipe:
    pipe_input: PipeInput
    pipe_output: PipeOutput
    comb_logic: List
    stages: List[Stage]

    def __init__(self, producer: PipeInput, consumer: PipeOutput):
        self.pipe_input = producer
        self.pipe_output = consumer
        self.comb_logic = []
        self.stages = []

    def get_stats(self):
        self.resolve()
        stats = {
            'nbr_nodes': 0,
            'nbr_zero_cylce_nodes': 0,
            'nbr_one_cylce_nodes': 0,
            'nbr_multiple_cylce_nodes': 0,
            'nbr_regs': 0,
            'nbr_stages': len(self.stages),
            'by_type': {}
        }
        already_visited = [self.pipe_input]
        to_visit = _OrderedSet(self.pipe_input.get_consumers())
        while len(to_visit) > 0:
            p = to_visit.pop()
            if p not in already_visited:
                if isinstance(p, _Node):
                    stats['nbr_nodes'] += 1
                    if p.name in stats['by_type']:
                        stats['by_type'][p.name] += 1
                    else:
                        stats['by_type'][p.name] = 1
                if isinstance(p, ZeroCycleNode):
                    stats['nbr_zero_cylce_nodes'] += 1
                elif isinstance(p, OneCycleNode):
                    stats['nbr_one_cylce_nodes'] += 1
                elif isinstance(p, MultipleCycleNode):
                    stats['nbr_multiple_cylce_nodes'] += 1

                if isinstance(p, Register):
                    stats['nbr_regs'] += 1

                already_visited.append(p)
                if isinstance(p, ProducerNode):
                    to_visit.update(p.get_consumers())
        return stats

    def add_to_stage(self, node: _Node):
        assert node.stage_index is not None

        while len(self.stages) <= node.stage_index:
            self.stages.append(Stage())
        self.stages[node.stage_index].add(node)

    @staticmethod
    def is_node_needed(node):
        """
        Checks if a node can be dropped because no node used by the PipeOutput needs it results.
        Returns False if the node can be safely dropped.
        """
        to_visit = _OrderedSet(node.get_consumers())
        while len(to_visit) > 0:
            node = to_visit.pop()
            if isinstance(node, PipeOutput):
                return True
            else:
                to_visit.update(node.get_consumers())
        return False

    def resolve(self):
        # TODO recognize circles and abort
        to_visit = _OrderedSet(self.pipe_input.get_consumers())
        while len(to_visit) > 0:
            node = to_visit.pop()
            if isinstance(node, PipeOutput):
                assert self.pipe_output == node
            elif not isinstance(node, _Node):
                raise NotImplementedError()

            if isinstance(node, _Node) and not Pipe.is_node_needed(node):
                # print('Dropped not needed node.')
                # Result not needed, remove this node
                for p in node.get_producers():
                    p.deregister_consumer(node)
                continue

            stage = 0
            for p in node.get_producers():
                lowest_possible_stage = _next_stage(p)
                if lowest_possible_stage is None:
                    to_visit.add(node)
                    break
                stage = max(stage, lowest_possible_stage)
            else:
                if isinstance(node, _Node):
                    if isinstance(node, MultipleCycleNode):
                        # Add PipelineNodes to last stage
                        node.stage_index = stage + (node.latency - 1)
                    else:
                        node.stage_index = stage

                    self.add_to_stage(node)
                    to_visit.update(node.get_consumers())
                elif isinstance(node, PipeOutput):
                    # Pipe output must be placed in own stage after all other
                    stage = len(self.stages)
                for name in node.get_inputs().keys():
                    if isinstance(node.get_inputs()[name], list):
                        for index in range(len(node.get_inputs()[name])):
                            try:
                                p = node.get_inputs()[name][index].get_producer()
                                for reg_stage in range(_next_stage(p), stage):
                                    value = node.get_inputs()[name][index]

                                    # Search if needed register is already present (other node created one already)
                                    for reg in self.stages[reg_stage].nodes:
                                        if isinstance(reg, Register) and reg.get_inputs()['default'] == value:
                                            break
                                    else:
                                        reg = Register(value)
                                        reg.stage_index = reg_stage
                                        self.add_to_stage(reg)
                                    node.replace_input_listel(name, index, reg)
                            except AttributeError:
                                continue
                    else:
                        try:
                            p = node.get_inputs()[name].get_producer()
                            for reg_stage in range(_next_stage(p), stage):
                                value = node.get_inputs()[name]

                                # Search if needed register is already present (other node created one already)
                                for reg in self.stages[reg_stage].nodes:
                                    if isinstance(reg, Register) and reg.get_inputs()['default'] == value:
                                        break
                                else:
                                    reg = Register(value)
                                    reg.stage_index = reg_stage
                                    self.add_to_stage(reg)
                                node.replace_input(name, reg)
                        except AttributeError:
                            continue

        return self.stages

    @block
    def create(self, clk, rst):
        if len(self.stages) == 0:
            self.resolve()
        pipe_instances = []

        self.pipe_input.set_pipe_busy(self.pipe_output.busy)

        for stage_id, stage in enumerate(self.stages):
            if stage_id == len(self.stages) - 1:
                # Last stage before Output
                self.pipe_output.set_stage_data_valid(stage.valid)

            # Data valid signal
            if stage_id == 0:
                # First stage after PipeInput
                pipe_instances.append(
                    valid_logic(clk, rst, self.pipe_input.valid, self.pipe_input.pipe_busy, stage.valid)
                )
            else:
                previous_valid = self.stages[stage_id - 1].valid
                pipe_instances.append(
                    valid_logic(clk, rst, previous_valid, False, stage.valid)
                )

            for node in stage.nodes:
                node_input = _DynamicInterface(**node.get_inputs())
                node_output = _DynamicInterface(**node.get_outputs())
                if isinstance(node, OneCycleNode) or isinstance(node, MultipleCycleNode):
                    instance = node.logic(clk, rst, node_input, node_output, **node.logic_kwargs)
                elif isinstance(node, ZeroCycleNode):
                    instance = node.logic(node_input, node_output, **node.logic_kwargs)
                else:
                    raise NotImplementedError()
                pipe_instances.append(instance)

        # Add additional output logic
        pipe_instances.append(self.pipe_output.create_logic(clk, rst, len(self.stages)))

        return pipe_instances


class ProducerNode(PipeSignal):
    _consumer_nodes: Set[ConsumerNode]
    _output_signals: Dict

    def __init__(self):
        super().__init__(producer=self)
        self._consumer_nodes = set()
        self._output_signals = {}

    def add_output(self, default: PipeSignal = None, **kwargs: Union[PipeSignal, List[PipeSignal]]):
        if default is not None:
            default.set_producer(self)
            self._output_signals['default'] = default
            self.update(default)

        for key, value in kwargs.items():
            if isinstance(value, list):
                for pipe_signal in value:
                    pipe_signal.set_producer(self)
            else:
                value.set_producer(self)

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
            return self._output_signals[name]
        raise AttributeError()


class ConsumerNode:
    _inputs: Dict

    def __init__(self):
        super().__init__()
        self._inputs = {}

    def _try_register(self, val):
        if isinstance(val, list):
            for el in val:
                try:
                    p = el.get_producer()
                    p.register_consumer(self)
                except AttributeError:
                    pass
        else:
            try:
                p = val.get_producer()
                p.register_consumer(self)
            except AttributeError:
                pass

    def add_inputs(self, **kwargs):
        for name, in_arg in kwargs.items():
            if name in self._inputs:
                self.replace_input(name, in_arg)
            else:
                self._try_register(in_arg)
                self._inputs[name] = in_arg

    def get_inputs(self):
        return self._inputs

    def replace_input(self, name, new_in):
        assert name in self._inputs
        old_in = self._inputs[name]
        assert not isinstance(old_in, list)

        # Register for new producers
        self._try_register(new_in)
        self._inputs[name] = new_in

        # Deregister for old producers
        try:
            p = old_in.get_producer()
            # Check if other input still needs this producer
            for other_p in self.get_producers():
                if other_p == p:
                    break
            else:
                p.deregister_consumer(self)
        except AttributeError:
            pass

    def replace_input_listel(self, name, index, new_in):
        assert name in self._inputs
        assert isinstance(self._inputs[name], list)
        assert index < len(self._inputs[name])
        el_in = self._inputs[name][index]

        # Register for new producers
        self._try_register(new_in)
        self._inputs[name][index] = new_in

        # Deregister for old producers
        try:
            p = el_in.get_producer()
            # Check if other input still needs this producer
            for other_p in self.get_producers():
                if other_p == p:
                    break
            else:
                p.deregister_consumer(self)
        except AttributeError:
            pass

    def get_producers(self) -> Set:
        producers = set()
        for in_arg in self._inputs.values():
            if isinstance(in_arg, list):
                for el in in_arg:
                    try:
                        p = el.get_producer()
                        producers.add(p)
                    except AttributeError:
                        continue
            else:
                try:
                    p = in_arg.get_producer()
                    producers.add(p)
                except AttributeError:
                    continue
        return producers


class _Node(ProducerNode, ConsumerNode):
    """
    An inner element of the pipeline.
    Should not be used directly, use OneCycleNode or ZeroCycleNode.
    """
    def __init__(self):
        super().__init__()

        self.logic = None
        self.logic_kwargs = {}
        self.stage_index = None
        self.name = 'N/A'

    def set_logic(self, logic, **kwargs):
        self.logic = logic
        self.logic_kwargs = kwargs

    def get_logic(self):
        return self.logic

    def get_logic_kwargs(self):
        return self.logic_kwargs

    def set_name(self, name):
        self.name = name


class ZeroCycleNode(_Node):
    """
    A combinatorical node of the pipeline. The logic must use only combinational logic.
    The complexety must be minimized. Intendet for low/no cost logic like shifting of signals.

    The provided logic must be of the following function signature:
        def logic(node_input, node_output)
    """
    def __init__(self):
        super().__init__()


class OneCycleNode(_Node):
    """
    A sequential node of the pipeline. The nodes logic must take exactly one clk cycle.

    The provided logic must be of the following function signature:
        def logic(clk, rst, stage, node_input, node_output)
    """
    def __init__(self):
        super().__init__()


class MultipleCycleNode(_Node):
    """
    A node implementating an inner pipeline.
    The nodes logic must take a constant number of clk cycles (latency) and must be pipelined internally.

    The provided logic must be of the following function signature:
        def logic(clk, stages: List, node_input, node_output)
    """
    def __init__(self, latency):
        super().__init__()
        assert latency > 0
        self.latency = latency


class PipeInput(ProducerNode):
    valid: SignalType
    pipe_busy: Optional[SignalType]

    def __init__(self, input_valid: SignalType, **raw_signals: Union[PipeSignal, List[PipeSignal]]):
        super().__init__()

        self.valid = input_valid
        self.pipe_busy = None

        self.add_output(**raw_signals)

    def set_pipe_busy(self, busy_signal):
        self.pipe_busy = busy_signal


class PipeOutput(ConsumerNode):
    busy: SignalType
    pipe_valid: SignalType
    _stage_data_valid: Optional[SignalType]
    _pipe_outputs: Optional[PackedReadStruct]

    def __init__(self, busy: SignalType, **inputs):
        super().__init__()

        self.busy = busy
        self.pipe_valid = Signal(bool(0))
        self.stage_data_valid = None
        self._pipe_outputs = None

        self.add_inputs(**inputs)

    def __getattr__(self, name):
        if hasattr(self._pipe_outputs, name):
            signal = getattr(self._pipe_outputs, name)
            if isinstance(signal, list):
                return list(signal)
            else:
                return signal
        raise AttributeError("%r object has no attribute %r" % (self.__class__.__name__, name))

    def set_stage_data_valid(self, valid_signal):
        self.stage_data_valid = valid_signal

    @block
    def create_logic(self, clk, rst, pipe_len):
        def nested_map(function, el):
            if isinstance(el, list):
                return [nested_map(function, subel) for subel in el]
            return function(el)

        data_desc = StructDescription.from_kwargs(
            'IntermediateStructDescription',
            **{k: nested_map(lambda x: BitVector(x.get_type()), pn) for k, pn in self._inputs.items()}
        )

        # input_vector = [s.get_signal() for s in self._inputs.values()]
        input_vector = PackedWriteStruct.create_signal_list(
            nested_map(lambda x: x.get_signal(), list(self._inputs.values()))
        )
        if len(input_vector) == 1:
            cache_input = input_vector[0]
        else:
            cache_input = ConcatSignal(*input_vector)
        cache_output = BitVector(len(data_desc)).create_instance()

        self._pipe_outputs = data_desc.create_read_instance(cache_output)
        out_insts = self._pipe_outputs.instances()

        producer = FifoProducer(BitVector(len(cache_input)).create_instance())
        consumer = FifoConsumer(BitVector(len(producer.data)).create_instance())
        bits_needed = len("{0:b}".format(pipe_len + 1)) + 1
        cache_fifo = fifo(clk, rst, producer, consumer, bits_needed)

        @always_seq(clk.posedge, reset=rst)
        def drive_data():
            producer.wr.next = False
            if not self.busy:
                if consumer.empty:
                    cache_output.next = cache_input.unsigned()
                    self.pipe_valid.next = self.stage_data_valid
                else:
                    cache_output.next = consumer.data
                    self.pipe_valid.next = True

            if self.stage_data_valid and (self.busy or not consumer.empty):
                producer.data.next = cache_input.unsigned()
                producer.wr.next = True

        @always_comb
        def drive_fifo_c():
            consumer.rd.next = not self.busy

        return instances()


class Register(OneCycleNode):
    def __init__(self, val):
        super().__init__()

        if isinstance(val, int):
            raise NotImplementedError()

        self.add_inputs(default=val)
        res = PipeSignal(val.get_type(), clone_signal(val.get_signal()))
        self.add_output(res)
        self.set_name('reg')

        self.logic = register


@block
def register(clk, rst, node_input, node_output):
    @always_seq(clk.posedge, reset=rst)
    def drive_data():
        node_output.default.next = node_input.default
    return instances()


class Stage:
    valid: SignalType
    nodes: Set[OneCycleNode]

    def __init__(self, nodes=None):
        self.valid = Signal(bool(0))
        if nodes is None:
            self.nodes = set()
        else:
            self.nodes = nodes

    def add(self, node):
        self.nodes.add(node)

    def __len__(self):
        return self.nodes.__len__()


@block
def valid_logic(clk, rst, valid_in, busy, valid_out):
    @always_seq(clk.posedge, reset=rst)
    def drive_data():
        valid_out.next = valid_in and not busy
    return instances()
