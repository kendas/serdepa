from unittest import TestCase

from serdepa.packets import SerdepaPacket
from serdepa.primitives import nx_int8, nx_int16


class Point(SerdepaPacket):
    x = nx_int8()
    y = nx_int16()


class SimplePacketTester(TestCase):
    def setUp(self):
        self.repr = b'\x00\x00\x01'

    def tearDown(self):
        del self.repr

    def test_deserialize(self):
        packet = Point.deserialize(self.repr)
        self.assertEqual(packet.x, 0)
        self.assertEqual(packet.y, 1)

    def test_serialize(self):
        packet = Point()
        packet.x = 0
        packet.y = 1
        self.assertEqual(packet.serialize(), self.repr)
