"""test_serdepa.py: Tests for serdepa packets. """

import unittest
from codecs import decode, encode

from serdepa import (
    SerdepaPacket, Length, List, Array, ByteString,
    nx_uint8, nx_uint16, nx_uint32, nx_uint64,
    nx_int8, nx_int16, nx_int32, nx_int64,
    uint8, uint16, uint32, uint64,
    int8, int16, int32, int64
)
from serdepa.exceptions import DeserializeError


__author__ = "Kaarel Ratas"
__license__ = "MIT"


class PointStruct(SerdepaPacket):
    x = nx_int32()
    y = nx_int32()


class OnePacket(SerdepaPacket):
    header = nx_uint8()
    timestamp = nx_uint32()
    length = Length(nx_uint8, "data")
    data = List(nx_uint8)
    tail = List(nx_uint8)


class SimpleFieldTester(unittest.TestCase):
    data = "0000000100000002"

    def test_simple_field_deserialize(self):
        packet = PointStruct.deserialize(decode(self.data, "hex"))

        self.assertEqual(packet.x, 1)
        self.assertEqual(packet.y, 2)


class ListTester(unittest.TestCase):
    data = "010000303904010203040506"

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

        self.assertEqual(p.serialize(), decode(self.data, "hex"))

    def test_two(self):
        p = OnePacket.deserialize(decode(self.data, "hex"))

        self.assertEqual(p.header, 1)
        self.assertEqual(p.timestamp, 12345)
        self.assertEqual(p.length, 4)
        self.assertEqual(len(p.data), 4)
        self.assertEqual(len(p.tail), 2)
        self.assertEqual(list(p.data), [1, 2, 3, 4])
        self.assertEqual(list(p.tail), [5, 6])
