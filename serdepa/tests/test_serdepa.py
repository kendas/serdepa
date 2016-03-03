"""test_serdepa.py: Tests for serdepa packets. """

import unittest

from serdepa import SerdepaPacket, Length, List, Array, \
        nx_uint8, nx_uint16, nx_uint32, nx_uint64, \
        nx_int8, nx_int16, nx_int32, nx_int64, \
        uint8, uint16, uint32, uint64


__author__ = "Raido Pahtma, Kaarel Ratas"
__license__ = "MIT"


class PointStruct(SerdepaPacket):
    _fields_ = [
        ("x", nx_int32),
        ("y", nx_int32)
    ]


class OnePacket(SerdepaPacket):
    _fields_ = [
        ("header", nx_uint8),
        ("timestamp", nx_uint32),
        ("length", Length(nx_uint8, "data")),
        ("data", List(nx_uint8)),
        ("tail", List(nx_uint8))
    ]


class DefaultValuePacket(SerdepaPacket):
    _fields_ = [
        ("header", nx_uint8, 1),
        ("timestamp", nx_uint32, 12345),
        ("length", Length(nx_uint8, "data")),
        ("data", List(nx_uint8), [1, 2, 3, 4]),
        ("tail", List(nx_uint8), [5, 6])
    ]


class AnotherPacket(SerdepaPacket):
    _fields_ = [
        ("header", nx_uint8),
        ("timestamp", nx_uint32),
        ("origin", PointStruct),
        ("points", Length(nx_uint8, "data")),
        ("data", List(PointStruct))
    ]


class ArrayPacket(SerdepaPacket):
    _fields_ = [
        ("header", nx_uint8),
        ("data", Array(PointStruct, 4))
    ]


class SimpleArray(SerdepaPacket):
    _fields_ = [
        ("data", Array(nx_uint8, 10))
    ]


class MyNodes(SerdepaPacket):
    _fields_ = [
        ("nodeId", nx_uint16),
        ("attr", nx_int16),
        ("inQlty", nx_uint8),
        ("outQlty", nx_uint8),
        ("qlty", nx_uint8),
        ("lifetime", nx_uint8)
    ]


class MyRouters(SerdepaPacket):
    _fields_ = [
        ("beatId", nx_uint32),
        ("routerId", nx_uint16),
        ("partnerId", nx_uint16),
        ("attr", nx_uint16),
        ("qlty", nx_uint8),
        ("lifetime", nx_uint8),
        ("flags", nx_uint8),
    ]


class BeatRecord(SerdepaPacket):
    _fields_ = [
        ("clockstamp", nx_uint32),
        ("nodes_in_beat", Length(nx_uint8, "nodes")),
        ("beats_in_cycle", Length(nx_uint8, "routers")),
        ("my_beat_id", nx_uint32),
        ("nodes", List(MyNodes)),
        ("routers", List(MyRouters))
    ]


class TransformTester(unittest.TestCase):
    p1 = "010000303904010203040506"

    def test_one(self):
        p = OnePacket()
        p.header = 1
        p.timestamp = 12345
        p.data.append(1)
        p.data.append(2)
        p.data.append(3)
        p.data.append(4)
        p.tail.append(5)
        p.tail.append(6)

        self.assertEqual(p.serialize(), self.p1.decode("hex"))

    def test_two(self):
        p = OnePacket()
        p.deserialize(self.p1.decode("hex"))

        self.assertEqual(p.header, 1)
        self.assertEqual(p.timestamp, 12345)
        self.assertEqual(p.length, 4)
        self.assertEqual(len(p.data), 4)
        self.assertEqual(len(p.tail), 2)
        self.assertEqual(list(p.data), [1, 2, 3, 4])
        self.assertEqual(list(p.tail), [5, 6])


class EmptyTailTester(unittest.TestCase):
    p1 = "01000030390401020304"

    def test_empty_tail_deserialize(self):
        p = OnePacket()
        p.deserialize(self.p1.decode("hex"))

        self.assertEqual(p.header, 1)
        self.assertEqual(p.timestamp, 12345)
        self.assertEqual(p.length, 4)
        self.assertEqual(list(p.data), [1, 2, 3, 4])
        self.assertEqual(list(p.tail), [])

    def test_empty_tail_serialize(self):
        p = OnePacket()
        p.header = 1
        p.timestamp = 12345
        p.data.append(1)
        p.data.append(2)
        p.data.append(3)
        p.data.append(4)

        self.assertEqual(p.serialize(), self.p1.decode("hex"))

class DefaultValueTester(unittest.TestCase):
    p1 = "010000303904010203040506"
    p2 = "020000303904010203040506"

    def test_default_value_serialize(self):
        p = DefaultValuePacket()
        self.assertEqual(p.serialize(), self.p1.decode("hex"))

    def test_default_keyword(self):
        p = DefaultValuePacket(header=2)
        self.assertEqual(p.serialize(), self.p2.decode("hex"))


class ArrayTester(unittest.TestCase):
    a1 = "00010203040506070809"
    a2 = "000000000100000002000000030000000400000005000000060000000000000000"

    def test_simple_array(self):
        p = SimpleArray()
        for i in xrange(10):
            p.data.append(i)
        self.assertEqual(p.serialize(), self.a1.decode("hex"))

    def test_single_array(self):
        p = ArrayPacket()
        p.header = 0
        p.data.append(PointStruct(x=1, y=2))
        p.data.append(PointStruct(x=3, y=4))
        p.data.append(PointStruct(x=5, y=6))

        self.assertEqual(p.serialize(), self.a2.decode("hex"))

    def test_single_array_deserialize(self):
        p = ArrayPacket()
        p.deserialize(self.a2.decode("hex"))

        self.assertEqual(p.header, 0)
        self.assertEqual(len(p.data), 4)
        self.assertEqual(p.data[1].x, 3)
        self.assertEqual(p.data[3].y, 0)


class TestHourlyReport(unittest.TestCase):
    report = "1DD26640070D0005029E022B0139FFFF0003029E010EFFFF3D0300000000FFFF000000000000FFFF000000000000FFFF000000000000FFFF000000000000FFFF000000000000000000000000000000000201AB029E01AB000000150000030296029E02350000001500000000000000000000000000000000000000000000000000000000000000000000000000000000000701FA022B022D00FF381300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

    def test_hourly_deserialize(self):
        r = BeatRecord()
        r.deserialize(self.report.decode("hex"))

        self.assertEqual(r.nodes_in_beat, 7)
        self.assertEqual(r.beats_in_cycle, 13)

class StringTester(unittest.TestCase):
    report = "1DD26640070D0005029E022B0139FFFF0003029E010EFFFF3D0300000000FFFF000000000000FFFF000000000000FFFF000000000000FFFF000000000000FFFF000000000000000000000000000000000201AB029E01AB000000150000030296029E02350000001500000000000000000000000000000000000000000000000000000000000000000000000000000000000701FA022B022D00FF381300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

    def test_str(self):
        r = BeatRecord()
        r.deserialize(self.report.decode("hex"))

        self.assertEqual(self.report, str(r))


class SerializedSizeTester(unittest.TestCase):
    def test_minimal_serialized_size(self):
        self.assertEqual(OnePacket.minimal_size(), 6)
        self.assertEqual(BeatRecord.minimal_size(), 10)

    def test_serialized_size(self):
        p = OnePacket()
        p.header = 1
        p.timestamp = 12345
        p.data.append(1)
        p.data.append(2)
        p.data.append(3)
        p.data.append(4)
        p.tail.append(5)
        p.tail.append(6)
        self.assertEqual(p.serialized_size(), 12)


class NestedPacketTester(unittest.TestCase):
    p = "F10000000000000003000000010000000200000002000000010000000300000000"

    def test_nested_packet_serialize(self):
        packet = ArrayPacket()
        packet.header = 0xF1
        for i, j in zip(xrange(4), reversed(xrange(4))):
            packet.data.append(PointStruct(x=i, y=j))
        self.assertEqual(packet.serialize(), self.p.decode("hex"))

    def test_nested_packet_deserialize(self):
        packet = ArrayPacket()
        packet.deserialize(self.p.decode("hex"))
        self.assertEqual(packet.header, 0xF1)
        self.assertEqual(
            list(packet.data),
            [
                PointStruct(x=0, y=3),
                PointStruct(x=1, y=2),
                PointStruct(x=2, y=1),
                PointStruct(x=3, y=0)
            ]
        )


if __name__ == '__main__':
    unittest.main()
