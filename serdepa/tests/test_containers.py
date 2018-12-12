from unittest import TestCase

from serdepa.packets import SerdepaPacket
from serdepa.primitives import nx_uint8, nx_uint16, nx_int8
from serdepa.containers import Length, List, Array
from serdepa.exceptions import ValidationError


class VariableLengthListPacket(SerdepaPacket):
    length = Length(nx_uint8(), 'list')
    list = List(nx_uint8)


class UnknownLengthListPacket(SerdepaPacket):
    irrelevant = nx_uint8()
    tail = List(nx_uint8)


class ArrayPacket(SerdepaPacket):
    irrelevant = nx_uint8()
    data = Array(nx_uint8, 3)


class AnotherArrayPacket(SerdepaPacket):
    irrelevant = nx_uint16()
    data = Array(nx_int8, 2)


class VariableLengthTester(TestCase):
    def setUp(self):
        self.repr = b'\x04\x01\x02\x03\x04'

    def tearDown(self):
        del self.repr

    def test_deserialize(self):
        packet = VariableLengthListPacket.deserialize(self.repr)
        self.assertEqual(packet.length, 4)
        self.assertEqual(packet.list, [1, 2, 3, 4])

    def test_serialize(self):
        packet = VariableLengthListPacket()
        packet.list = [1, 2, 3, 4]
        self.assertEqual(packet.serialize(), self.repr)


class ArrayTester(TestCase):
    def setUp(self):
        self.repr = b'\x01\x02\xDD\xFF'

    def tearDown(self):
        del self.repr

    def test_deserialize(self):
        packet = ArrayPacket.deserialize(self.repr)
        self.assertEqual(packet.irrelevant, 1)
        self.assertEqual(packet.data, [2, 0xDD, 0xFF])

        packet = AnotherArrayPacket.deserialize(self.repr)
        self.assertEqual(packet.irrelevant, 0x102)
        self.assertEqual(packet.data, [-35, -1])

    def test_serialize(self):
        packet = ArrayPacket()
        packet.irrelevant = 1
        packet.data = [2, 0xDD, 0xFF]
        self.assertEqual(packet.serialize(), self.repr)

        packet = AnotherArrayPacket()
        packet.irrelevant = 0x102
        packet.data = [-35, -1]
        self.assertEqual(packet.serialize(), self.repr)

    def test_contains(self):
        test_list = [0, 0, 255]

        packet = ArrayPacket()
        packet.data = test_list
        self.assertIsNot(packet.data, test_list)
        self.assertIn(0, packet.data)
        self.assertIn(255, packet.data)
        self.assertNotIn(-1, packet.data)
        self.assertNotIn(127, packet.data)

    def test_setitem(self):
        packet = ArrayPacket()

        packet.data[0] = 2
        packet.data[1] = 0xDD
        packet.data[2] = 0xFF

        self.assertEqual(packet.data, [2, 0xDD, 0xFF])
        with self.assertRaises(IndexError):
            packet.data[3] = 65

    def test_validation(self):
        packet = ArrayPacket()

        packet.data = [2, 0xDD, 0xFF]
        with self.assertRaises(ValidationError):
            packet.data = []
        with self.assertRaises(ValidationError):
            packet.data = [1, 2, 3, 4]
        with self.assertRaises(ValidationError):
            packet.data[0] = 256

    def test_initialization_default(self):
        packet = ArrayPacket(data=[2, 0xDD, 0xFF])

        self.assertEqual(packet.data, [2, 0xDD, 0xFF])

    def test_slice(self):
        packet = ArrayPacket()
        packet.data = [2, 0xDD, 0xFF]
        self.assertEqual(packet.data[:2], [2, 0xDD])
        self.assertEqual(packet.data[::2], [2, 0xFF])


class SimpleTailListTester(TestCase):
    def setUp(self):
        self.repr = b'\x01\x02\x03\x04'

    def tearDown(self):
        del self.repr

    def test_deserialize(self):
        packet = UnknownLengthListPacket.deserialize(self.repr)
        self.assertEqual(packet.irrelevant, 1)
        self.assertEqual(packet.tail, [2, 3, 4])

    def test_serialize(self):
        packet = UnknownLengthListPacket()
        packet.irrelevant = 1
        packet.tail = [2, 3, 4]
        self.assertEqual(packet.serialize(), self.repr)
