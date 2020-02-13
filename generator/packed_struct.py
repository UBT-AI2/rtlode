import inspect

from myhdl import Signal, intbv, SignalType, ConcatSignal


class _PackedStruct:
    def __init__(self, fields):
        self._fields = fields
        for name, value in fields.items():
            setattr(self, name, value)

    def __len__(self):
        nbr_bits = 0
        for name in self._fields:
            nbr_bits += len(self._fields[name])
        return nbr_bits


class PackedReadStruct(_PackedStruct):
    def __init__(self, fields, data):
        high_index = len(data)
        for name, value in fields.items():
            low_index = high_index - len(value)
            data_slice = data(high_index, low_index)
            high_index = low_index

            if isinstance(value, BitVector):
                fields[name] = data_slice
            elif issubclass(value, StructDescription):
                fields[name] = value.create_read_instance(data_slice)
        super().__init__(fields)


class PackedWriteStruct(_PackedStruct):
    def __init__(self, fields):
        for name, value in fields.items():
            if isinstance(value, BitVector):
                fields[name] = value.create_instance()
            elif issubclass(value, StructDescription):
                fields[name] = value.create_write_instance()
        super().__init__(fields)

    def packed(self):
        bitvector = []
        for name, value in self._fields.items():
            if isinstance(value, SignalType):
                bitvector.append(value)
            elif isinstance(value, PackedWriteStruct):
                bitvector.append(value.packed())
            else:
                raise Exception('Unsupported field type in PackedWriteStruct obj.')
        if len(bitvector) == 0:
            raise Exception('Empty PackedSignals obj.')
        return ConcatSignal(*bitvector)


class BitVector:
    def __init__(self, nbr_bits):
        self._nbr_bits = nbr_bits

    def __len__(self):
        return self._nbr_bits

    def create_instance(self):
        return Signal(intbv(0)[self._nbr_bits:0])


class _LengthMetaclass(type):
    def __len__(self):
        return self.len()


class StructDescription(metaclass=_LengthMetaclass):
    @classmethod
    def len(cls):
        cls._check_wellformness()
        length = 0
        for _, value in cls._get_props().items():
            length += len(value)
        return length

    @classmethod
    def _get_props(cls):
        return {k: v for k, v in vars(cls).items() if not k.startswith("__")}

    @classmethod
    def _check_wellformness(cls):
        for name, value in cls._get_props().items():
            if isinstance(value, BitVector):
                continue
            elif inspect.isclass(value) and issubclass(value, StructDescription):
                continue
            else:
                raise Exception('Unsupported field type in StructDescription.')
        return True

    @classmethod
    def create_read_instance(cls, data: SignalType) -> PackedReadStruct:
        if not isinstance(data, SignalType) or not isinstance(data.val, intbv):
            raise Exception('PackedReadStruct data must be of type intbv.')
        cls._check_wellformness()

        if len(data) != len(cls):
            raise Exception('PackedReadStruct data must be the size of StructDescription.')
        return PackedReadStruct(cls._get_props(), data)

    @classmethod
    def create_write_instance(cls) -> PackedWriteStruct:
        cls._check_wellformness()

        return PackedWriteStruct(cls._get_props())
