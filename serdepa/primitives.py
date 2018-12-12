"""
This file houses the primitive field types for the SerDePa library.
This includes the integer types
"""
import struct

import six

from .base import BaseField
from .exceptions import DeserializeError, ValidationError
from .singletons import DEFAULT


class BaseInt(BaseField):
    """
    Base class for all integer types.
    Has _signed (bool) and _format (struct format string).
    """

    _length = None
    _signed = None
    _format = ""
    _default = 0

    def __init__(self, default=DEFAULT):
        super(BaseInt, self).__init__()
        if default is not DEFAULT:
            for validator in self._validators:
                validator(default)
            self._default = default

    def to_bytes(self, parent):
        return struct.pack(self._format, self._get_value(parent))

    def from_bytes(self, buffer, parent):
        """

        :param six.BytesIO buffer:
        :param parent:
        :return:
        """
        value = buffer.read(self._length // 8)
        if len(value) < self._length // 8:
            raise DeserializeError("Input too short")
        else:
            python_value, = struct.unpack(self._format, value)
            self._set_value(parent, python_value)
        return buffer.tell() >= len(buffer.getvalue())

    def __get__(self, instance, owner):
        print("In __get__ of {}".format(self.__repr__))
        return self._get_value(instance)

    def __set__(self, instance, value):
        print("In __set__ of {}".format(self.__repr__))
        self._set_value(instance, value)

    def _get_value(self, parent):
        return parent._field_values[self._init_order]

    def _set_value(self, parent, value):
        if value is DEFAULT:
            value = self._default
        self.validate(value)
        parent._field_values[self._init_order] = value

    def _validate_range(self, value):
        number_range = (1 << self._length) - 1
        if self._signed:
            minimum = -1 * (number_range // 2) - 1
            maximum = number_range // 2
        else:
            minimum = 0
            maximum = number_range
        if not (minimum <= value <= maximum):
            raise ValidationError("Value {} is out of range for {}".format(
                value, self.__class__.__name__)
            )

    def _validate_type(self, value):
        if not isinstance(value, int):
            raise ValidationError("Invalid type value {} for {}".format(
                value, self.__class__.__name__)
            )

    @property
    def _validators(self):
        return [self._validate_type, self._validate_range]


class nx_uint8(BaseInt):
    _signed = False
    _length = 8
    _format = ">B"


class nx_int8(BaseInt):
    _signed = True
    _length = 8
    _format = ">b"


class uint8(BaseInt):
    _signed = False
    _length = 8
    _format = "<B"


class int8(BaseInt):
    _signed = True
    _length = 8
    _format = "<b"


class nx_uint16(BaseInt):
    _signed = False
    _length = 16
    _format = ">H"


class nx_int16(BaseInt):
    _signed = True
    _length = 16
    _format = ">h"


class uint16(BaseInt):
    _signed = False
    _length = 16
    _format = "<H"


class int16(BaseInt):
    _signed = True
    _length = 16
    _format = "<h"


class nx_uint32(BaseInt):
    _signed = False
    _length = 32
    _format = ">I"


class nx_int32(BaseInt):
    _signed = True
    _length = 32
    _format = ">i"


class uint32(BaseInt):
    _signed = False
    _length = 32
    _format = "<I"


class int32(BaseInt):
    _signed = True
    _length = 32
    _format = "<i"


class nx_uint64(BaseInt):
    _signed = False
    _length = 64
    _format = ">Q"


class nx_int64(BaseInt):
    _signed = True
    _length = 64
    _format = ">q"


class uint64(BaseInt):
    _signed = False
    _length = 64
    _format = "<Q"


class int64(BaseInt):
    _signed = True
    _length = 64
    _format = "<q"
