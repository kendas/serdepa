from unittest import TestCase

from mock import MagicMock

from six import BytesIO

from serdepa.primitives import (
    int8, nx_int8, int16, nx_int16, int32, nx_int32, int64, nx_int64,
    uint8, nx_uint8, uint16, nx_uint16, uint32, nx_uint32, uint64, nx_uint64
)
from serdepa.exceptions import ValidationError, DeserializeError


class PrimitiveTypeTester(TestCase):
    max = NotImplemented
    min = NotImplemented
    type = NotImplemented

    def _get_value(self):
        return self.container_mock._field_values[self.field._init_order]

    def _set_value(self, value):
        self.container_mock._field_values[self.field._init_order] = value

    def _init_container_mock(self):
        self.container_mock.reset_mock()
        self.container_mock._field_values = {}

    def setUp(self):
        self.field = self.type()
        self.container_mock = MagicMock()
        self._init_container_mock()

    def tearDown(self):
        del self.field
        del self.container_mock


class Int8Tester(PrimitiveTypeTester):
    max = 127
    min = -128
    type = int8

    def test_set_value(self):
        self.field.__set__(self.container_mock, 1)
        self.assertEqual(self._get_value(), 1)

    def test_get_value(self):
        self._set_value(1)
        self.assertEqual(self.field.__get__(self.container_mock, MagicMock), 1)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max + 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min - 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, '1')

    def test_to_bytes(self):
        self._set_value(1)
        self.assertEqual(self.field.to_bytes(self.container_mock), b'\x01')

    def test_from_bytes(self):
        buffer = BytesIO(b'\xFF')

        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), -1)

        self._init_container_mock()
        buffer = BytesIO(b'\x80')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), -128)


class NxInt8Tester(PrimitiveTypeTester):
    max = 127
    min = -128
    type = nx_int8

    def test_set_value(self):
        self.field.__set__(self.container_mock, 1)
        self.assertEqual(self._get_value(), 1)

    def test_get_value(self):
        self._set_value(1)
        self.assertEqual(self.field.__get__(self.container_mock, MagicMock), 1)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max + 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min - 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, '1')

    def test_to_bytes(self):
        self._set_value(1)
        self.assertEqual(self.field.to_bytes(self.container_mock), b'\x01')

    def test_from_bytes(self):
        buffer = BytesIO(b'\xFF')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), -1)

        self._init_container_mock()
        buffer = BytesIO(b'\x80')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), -128)


class Uint8Tester(PrimitiveTypeTester):
    max = 255
    min = 0
    type = uint8

    def test_set_value(self):
        self.field.__set__(self.container_mock, 1)
        self.assertEqual(self._get_value(), 1)

    def test_get_value(self):
        self._set_value(1)
        self.assertEqual(self.field.__get__(self.container_mock, MagicMock), 1)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, -1 * self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max + 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min - 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, '1')

    def test_to_bytes(self):
        self._set_value(1)
        self.assertEqual(self.field.to_bytes(self.container_mock), b'\x01')

    def test_from_bytes(self):
        buffer = BytesIO(b'\xFF')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 255)

        self._init_container_mock()
        buffer = BytesIO(b'\x80')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 128)


class NxUInt8Tester(PrimitiveTypeTester):
    max = 255
    min = 0
    type = nx_uint8

    def test_set_value(self):
        self.field.__set__(self.container_mock, 1)
        self.assertEqual(self._get_value(), 1)

    def test_get_value(self):
        self._set_value(1)
        self.assertEqual(self.field.__get__(self.container_mock, MagicMock), 1)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, -1 * self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max + 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min - 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, '1')

    def test_to_bytes(self):
        self._set_value(1)
        self.assertEqual(self.field.to_bytes(self.container_mock), b'\x01')

    def test_from_bytes(self):
        buffer = BytesIO(b'\xFF')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 255)

        self._init_container_mock()
        buffer = BytesIO(b'\x80')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 128)


class Int16Tester(PrimitiveTypeTester):
    max = 32767
    min = -32768
    type = int16

    def test_set_value(self):
        self.field.__set__(self.container_mock, 1)
        self.assertEqual(self._get_value(), 1)

    def test_get_value(self):
        self._set_value(1)
        self.assertEqual(self.field.__get__(self.container_mock, MagicMock), 1)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max + 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min - 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, '1')

    def test_to_bytes(self):
        self._set_value(1)
        self.assertEqual(self.field.to_bytes(self.container_mock), b'\x01\x00')

    def test_from_bytes(self):
        buffer = BytesIO(b'\xFF\x00')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 255)

        self._init_container_mock()
        buffer = BytesIO(b'\x00\x80')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), -32768)

        self._init_container_mock()
        buffer = BytesIO(b'\xFF')
        with self.assertRaises(DeserializeError):
            self.field.from_bytes(buffer, self.container_mock)


class NxInt16Tester(PrimitiveTypeTester):
    max = 32767
    min = -32768
    type = nx_int16

    def test_set_value(self):
        self.field.__set__(self.container_mock, 1)
        self.assertEqual(self._get_value(), 1)

    def test_get_value(self):
        self._set_value(1)
        self.assertEqual(self.field.__get__(self.container_mock, MagicMock), 1)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max + 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min - 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, '1')

    def test_to_bytes(self):
        self._set_value(1)
        self.assertEqual(self.field.to_bytes(self.container_mock), b'\x00\x01')

    def test_from_bytes(self):
        buffer = BytesIO(b'\x00\xFF')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 255)

        buffer = BytesIO(b'\x80\x00')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), -32768)

        buffer = BytesIO(b'\xFF')
        with self.assertRaises(DeserializeError):
            self.field.from_bytes(buffer, self.container_mock)


class Uint16Tester(PrimitiveTypeTester):
    max = 65535
    min = 0
    type = uint16

    def test_set_value(self):
        self.field.__set__(self.container_mock, 1)
        self.assertEqual(self._get_value(), 1)

    def test_get_value(self):
        self._set_value(1)
        self.assertEqual(self.field.__get__(self.container_mock, MagicMock), 1)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, -1 * self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max + 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min - 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, '1')

    def test_to_bytes(self):
        self._set_value(1)
        self.assertEqual(self.field.to_bytes(self.container_mock), b'\x01\x00')

    def test_from_bytes(self):
        buffer = BytesIO(b'\xFF\x00')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 255)

        buffer = BytesIO(b'\x00\x80')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 0x8000)

        buffer = BytesIO(b'\xFF')
        with self.assertRaises(DeserializeError):
            self.field.from_bytes(buffer, self.container_mock)


class NxUint16Tester(PrimitiveTypeTester):
    max = 65535
    min = 0
    type = nx_uint16

    def test_set_value(self):
        self.field.__set__(self.container_mock, 1)
        self.assertEqual(self._get_value(), 1)

    def test_get_value(self):
        self._set_value(1)
        self.assertEqual(self.field.__get__(self.container_mock, MagicMock), 1)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, -1 * self.max * 2)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.max + 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, self.min - 1)
        with self.assertRaises(ValidationError):
            self.field.__set__(self.container_mock, '1')

    def test_to_bytes(self):
        self._set_value(1)
        self.assertEqual(self.field.to_bytes(self.container_mock), b'\x00\x01')

    def test_from_bytes(self):
        buffer = BytesIO(b'\x00\xFF')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 255)

        buffer = BytesIO(b'\x80\x00')
        self.assertTrue(self.field.from_bytes(buffer, self.container_mock))
        self.assertEqual(self._get_value(), 0x8000)

        buffer = BytesIO(b'\xFF')
        with self.assertRaises(DeserializeError):
            self.field.from_bytes(buffer, self.container_mock)
