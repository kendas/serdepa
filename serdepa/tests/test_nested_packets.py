from unittest import TestCase

from serdepa.packets import SerdepaPacket
from serdepa.primitives import nx_int8, nx_uint8


class Header(SerdepaPacket):
    type = nx_uint8()


class Data(SerdepaPacket):
    header = Header()
    event_count = nx_int8()
    false_alarm_count = nx_int8()


class SimplePacketTester(TestCase):
    def setUp(self):
        self.repr = b'\x05\x00\x01'

    def tearDown(self):
        del self.repr

    def test_deserialize(self):
        packet = Data.deserialize(self.repr)
        self.assertEqual(packet.header.type, 5)
        self.assertEqual(packet.event_count, 0)
        self.assertEqual(packet.false_alarm_count, 1)

    def test_serialize(self):
        packet = Data()
        packet.header.type = 5
        packet.event_count = 0
        packet.false_alarm_count = 1
        self.assertEqual(packet.serialize(), self.repr)
