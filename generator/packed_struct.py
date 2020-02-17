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
    """
    Used to describe a read instance of a StructDescription.
    """
    def __init__(self, fields, data, high_lim, low_lim):
        if isinstance(data, PackedReadStruct):
            data = data._data
        self._data = data
        self._high_lim = high_lim
        self._low_lim = low_lim

        high_index = high_lim
        for name, value in fields.items():
            low_index = high_index - len(value)
            if low_index < low_lim:
                raise Exception('PackedReadStruct trying to access data below lower limit.')

            if isinstance(value, BitVector):
                fields[name] = data(high_index, low_index)
            elif issubclass(value, StructDescription):
                fields[name] = value.create_read_instance(data, high_index, low_index)

            high_index = low_index
        super().__init__(fields)

    def high_lim(self):
        return self._high_lim

    def low_lim(self):
        return self._low_lim


class PackedWriteStruct(_PackedStruct):
    """
    Used to describe a write instance of a StructDescription.
    """
    def __init__(self, fields):
        for name, value in fields.items():
            if isinstance(value, BitVector):
                fields[name] = value.create_instance()
            elif issubclass(value, StructDescription):
                fields[name] = value.create_write_instance()
        super().__init__(fields)

    def packed(self):
        bitvector = self._packed()

        if len(bitvector) == 0:
            raise Exception('Empty PackedSignals obj.')
        elif len(bitvector) == 1:
            return bitvector[0]
        else:
            return ConcatSignal(*bitvector)

    def _packed(self):
        """
        Returns a ConcatSignal following the signals of the struct.
        :return: concatted signal
        """
        bitvector = []
        for name, value in self._fields.items():
            if isinstance(value, SignalType):
                bitvector.append(value)
            elif isinstance(value, PackedWriteStruct):
                bitvector.extend(value._packed())
            else:
                raise Exception('Unsupported field type in PackedWriteStruct obj.')
        return bitvector


class BitVector:
    """
    Can be used to describe a bitfield in a StructDescription.
    """
    def __init__(self, nbr_bits):
        self._nbr_bits = nbr_bits

    def __len__(self):
        return self._nbr_bits

    def create_instance(self):
        """
        Creates a signal which can be used as representation of given BitVector.
        :return: signal representation
        """
        return Signal(intbv(0)[self._nbr_bits:0])


class _LengthMetaclass(type):
    """
    Internal metaclass allowing the use of len() on StructDescription classes.
    """
    def __len__(self):
        return self.len()


class StructDescription(metaclass=_LengthMetaclass):
    """
    Used to describe a PackedStructure.
    Class attributes can either be a BitVector or other StructDescriptions.

    As Example:
        class CcipRx(StructDescription):
            c0TxAlmFull = BitVector(1)
            c1TxAlmFull = BitVector(1)
            c0 = CcipC0Rx
            c1 = CcipC1Rx
    """
    @classmethod
    def len(cls):
        """
        Returns the number of bits of the descripted struct.
        :return: number of bits
        """
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
    def create_read_instance(cls, data: SignalType, high_lim=None, low_lim=None) -> PackedReadStruct:
        """
        Creates a read instance of a described structure.
        :param data: raw data to be mapped on struct
        :param high_lim: Upper limit for data access
        :param low_lim: Lower limit for data access
        :return: nested struct following the described structure
        """
        if not isinstance(data, PackedReadStruct)\
                and (not isinstance(data, SignalType) or not isinstance(data.val, intbv)):
            raise Exception('PackedReadStruct data must be of type intbv.')
        cls._check_wellformness()

        if not high_lim:
            if isinstance(data, PackedReadStruct):
                high_lim = data.high_lim()
            else:
                high_lim = len(data)
        if not low_lim:
            if isinstance(data, PackedReadStruct):
                low_lim = data.low_lim()
            else:
                low_lim = 0

        if high_lim - low_lim != len(cls):
            raise Exception('PackedReadStruct data must be the size of StructDescription.')
        return PackedReadStruct(cls._get_props(), data, high_lim, low_lim)

    @classmethod
    def create_write_instance(cls) -> PackedWriteStruct:
        """
        Creates a written instance of the a described structure.
        :return: nested struct following the described structure
        """
        cls._check_wellformness()

        return PackedWriteStruct(cls._get_props())
