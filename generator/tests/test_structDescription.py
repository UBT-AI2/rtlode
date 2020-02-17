from unittest import TestCase

from myhdl import intbv, Signal

from generator.packed_struct import StructDescription, BitVector


class TestA(StructDescription):
    a = BitVector(1)
    b = BitVector(5)


class TestB(StructDescription):
    a = BitVector(2)
    b = BitVector(1)
    c = TestA


class TestC(StructDescription):
    a = BitVector(2)
    b = BitVector(3)


class TestMalformed(StructDescription):
    a = 4


class TestStructDescription(TestCase):
    def test_len(self):
        self.assertEqual(6, len(TestA))
        self.assertEqual(9, len(TestB))

    def test__get_props(self):
        self.assertEqual(2, len(TestA._get_props()))
        self.assertEqual(3, len(TestB._get_props()))
        self.assertEqual(TestA, TestB._get_props()['c'])

    def test__check_wellformness(self):
        self.assertTrue(TestA._check_wellformness())
        self.assertTrue(TestB._check_wellformness())
        self.assertRaises(Exception, TestMalformed._check_wellformness)

    def test_create_read_instance(self):
        data = intbv(0)[6:0]
        data[6:5] = 1
        data[5:0] = 4
        read_inst = TestA.create_read_instance(Signal(data))
        self.assertEqual(1, read_inst.a)
        self.assertEqual(4, read_inst.b)

        data = intbv(0)[9:0]
        data[9:7] = 3
        data[7:6] = 0
        data[6:5] = 1
        data[5:0] = 4
        read_inst = TestB.create_read_instance(Signal(data))
        self.assertEqual(3, read_inst.a)
        self.assertEqual(0, read_inst.b)
        self.assertEqual(1, read_inst.c.a)
        self.assertEqual(4, read_inst.c.b)

        data = intbv(0)[9:0]
        self.assertRaises(Exception, TestA.create_read_instance, data)

    def test_create_write_instance(self):
        write_inst = TestA.create_write_instance()
        write_inst.a.next = 1
        write_inst.a._update()
        write_inst.b.next = 5
        write_inst.b._update()
        write_sig = write_inst.packed()

        self.assertEqual(1, write_sig[6:5])
        self.assertEqual(5, write_sig[5:0])

        write_inst = TestB.create_write_instance()
        write_inst.a.next = 2
        write_inst.a._update()
        write_inst.b.next = 0
        write_inst.b._update()
        write_inst.c.a.next = 1
        write_inst.c.a._update()
        write_inst.c.b.next = 6
        write_inst.c.b._update()
        write_sig = write_inst.packed()

        self.assertEqual(2, write_sig[9:7])
        self.assertEqual(0, write_sig[7:6])
        self.assertEqual(1, write_sig[6:5])
        self.assertEqual(6, write_sig[5:0])

    def test_create_read_instace_nested(self):
        data = intbv(0)[6:0]
        data[6:5] = 1
        data[5:3] = 2
        data[3:0] = 5
        read_a_inst = TestA.create_read_instance(Signal(data))
        read_c_inst = TestC.create_read_instance(read_a_inst.b)

        self.assertEqual(2, read_c_inst.a)
        self.assertEqual(5, read_c_inst.b)
