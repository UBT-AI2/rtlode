from __future__ import annotations

from typing import List, Set, Dict, Iterable, Optional, Union

from myhdl import SignalType, Signal, block, instances, always_seq, always_comb

from generator.utils import clone_signal
from utils import num
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
            'nbr_seq_nodes': 0,
            'nbr_comb_nodes': 0,
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
                if isinstance(p, OneCycleNode):
                    stats['nbr_seq_nodes'] += 1
                elif isinstance(p, ZeroCycleNode):
                    stats['nbr_comb_nodes'] += 1

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
                print('Dropped not needed node.')
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

    def get_control_signals(self, stage_id):
        stage = self.stages[stage_id]

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

        return previous_valid, next_busy

    @block
    def create(self, clk, rst):
        if len(self.stages) == 0:
            self.resolve()
        stage_instances = []

        for stage_id, stage in enumerate(self.stages):
            previous_valid, next_busy = self.get_control_signals(stage_id)

            stage_instances.append(
                stage_logic(clk, rst, stage, previous_valid, next_busy)
            )
            for node in stage.nodes:
                node_input = _DynamicInterface(**node.get_inputs())
                node_output = _DynamicInterface(**node.get_outputs())
                if isinstance(node, OneCycleNode):
                    instance = node.logic(clk, rst, stage, node_input, node_output, **node.logic_kwargs)
                elif isinstance(node, MultipleCycleNode):
                    in_stage_id = stage_id - (node.latency - 1)
                    in_stage_valid, _ = self.get_control_signals(in_stage_id)
                    in_stage_busy = self.stages[in_stage_id].busy
                    out_stage_valid = stage.valid
                    out_stage_busy = next_busy
                    instance = node.logic(
                        clk, rst,
                        in_stage_valid, in_stage_busy,
                        out_stage_valid, out_stage_busy,
                        node_input, node_output,
                        **node.logic_kwargs
                    )
                elif isinstance(node, ZeroCycleNode):
                    instance = node.logic(node_input, node_output, **node.logic_kwargs)
                else:
                    raise NotImplementedError()
                stage_instances.append(instance)

        return stage_instances


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
    pipe_valid: Optional[SignalType]

    def __init__(self, busy: SignalType, **inputs):
        super().__init__()

        self.busy = busy
        self.pipe_valid = None

        self.add_inputs(**inputs)

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
        raise AttributeError("%r object has no attribute %r" % (self.__class__.__name__, name))

    def set_pipe_valid(self, valid_signal):
        self.pipe_valid = valid_signal


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
def register(clk, rst, stage, node_input, node_output):
    reg_data = clone_signal(node_output.default)

    @always_seq(clk.posedge, reset=rst)
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
    nodes: Set[OneCycleNode]

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
        if rst:
            stage.busy.next = False
            stage.valid.next = False
        elif not out_busy:
            # Next stage not busy
            if not stage.busy:
                # Buffer empty
                stage.valid.next = in_valid
            else:
                # Push buffer data out
                stage.valid.next = True

            # Consumer not busy
            stage.busy.next = False
        elif not stage.valid:
            # Just pass valid signals
            stage.valid.next = in_valid
            stage.busy.next = False

        elif in_valid and not stage.busy:
            stage.busy.next = in_valid and stage.valid

    @always_comb
    def flag_driver():
        stage.data2out.next = False
        stage.reg2out.next = False
        stage.data2reg.next = False
        if not out_busy:
            if not stage.busy:
                stage.data2out.next = True
            else:
                stage.reg2out.next = True
        elif not stage.valid:
            stage.data2out.next = True

        if not stage.busy:
            stage.data2reg.next = True

    return instances()
