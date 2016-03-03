"""serdepa.py: Binary packet serialization and deserialization library. """

import StringIO
import struct
import collections
import warnings
import copy
import math


__author__ = "Raido Pahtma, Kaarel Ratas"
__license__ = "MIT"


def add_property(cls, attr, attr_type):
    if hasattr(cls, attr):
        # print "NOT adding property %s to %s" % (attr, cls)
        # In the final version this should probably raise an exception once everything is handled properly
        pass
    else:

        if isinstance(attr_type, BaseIterable):
            setter = None

            def getter(self):
                return getattr(self, '_%s' % attr)

        elif isinstance(attr_type, Length):
            setter = None

            def getter(self):
                return len(getattr(
                    self,
                    '_field_registry'
                )[getattr(self, '_depends')[attr]])

        else:
            def setter(self, v):
                setattr(getattr(self, '_%s' % attr), "value", v)

            def getter(self):
                return getattr(self, '_%s' % attr).value

        setattr(cls, attr, property(getter, setter))


class SuperSerdepaPacket(type):
    """
    Metaclass of the SerdepaPacket object. Essentially does the following:
        Reads the _fields_ attribute of the class and for each 2- or 3-tuple entry
        sets up the properties of the class to the right names. Also checks that each
        (non-last) List instance has a Length field associated with it.
    """

    def __init__(cls, what, bases=None, attrs=None):

        setattr(cls, "_fields", collections.OrderedDict())
        setattr(cls, "_depends", dict())
        if '_fields_' in attrs:
            for field in attrs['_fields_']:
                if len(field) == 2 or len(field) == 3:
                    if len(field) == 2:
                        default = None
                    elif isinstance(field[1], Length):
                        raise TypeError("A Length field can't have a default value: {}".format(field))
                    else:
                        default = field[2]
                    add_property(cls, field[0], field[1])
                    getattr(cls, "_fields")[field[0]] = [field[1], default]
                    if isinstance(field[1], Length):
                        getattr(cls, "_depends")[field[0]] = field[1]._field
                    elif isinstance(field[1], List):
                        if not (field[0] in getattr(cls, "_depends").values() or field == attrs['_fields_'][-1]):
                            raise TypeError("Only the last field can have an undefined length ({} of type {})".format(
                                field[0],
                                type(field[1])
                            ))
                else:
                    raise TypeError("A field needs both a name and a type: {}".format(field))

        super(SuperSerdepaPacket, cls).__init__(what, bases, attrs)


class SerdepaPacket(object):
    """
    The superclass for any packets. Defining a subclass works as such:
        class Packet(SerdepaPacket):
            _fields_ = [
                ("name", type[, default]),
                ("name", type[, default]),
                ...
            ]

    Has the following public methods:
    .serialize() -> bytearray
    .deserialize(bytearray)

    and the class method
    .minimal_size() -> int
    """


    __metaclass__ = SuperSerdepaPacket

    def __init__(self, **kwargs):
        self._field_registry = collections.OrderedDict()
        for name, (_type, default) in self._fields.iteritems():
            if name in kwargs:
                self._field_registry[name] = _type(initial=copy.copy(kwargs[name]))
            elif default:
                self._field_registry[name] = _type(initial=copy.copy(default))
            else:
                self._field_registry[name] = _type()
            setattr(self, '_%s' % name, self._field_registry[name])

    def serialize(self):
        # TODO loop over _fields_ and serialize them
        serialized = StringIO.StringIO()
        for name, field in self._field_registry.iteritems():
            if name in self._depends:
                serialized.write(
                    field.serialize(self._field_registry[self._depends[name]].length)
                )
            else:
                serialized.write(field.serialize())
        ret = serialized.getvalue()
        serialized.close()
        return ret

    def deserialize(self, data, pos=0):
        # TODO loop over _fields_ and deserialize their values from data
        for i, (name, field) in enumerate(self._field_registry.iteritems()):
            if pos >= len(data):
                if i == len(self._field_registry) - 1 and isinstance(field, List):
                    return pos
                else:
                    raise AttributeError("Invalid length of data to deserialize.")
            try:
                pos = field.deserialize(data, pos)
            except IOError:
                length = 0
                for key, value in self._depends.iteritems():
                    if name == value:
                        pos = field.deserialize(data, pos, self._field_registry[key]._type.value)
                        break
                else:
                    pos = field.deserialize(data, pos, -1)
            if pos > len(data):
                raise AttributeError("Invalid length of data to deserialize.")
#        else:
#            if pos != len(data):
#                warnings.warn(RuntimeWarning("Data longer than available fields"))
        return pos

    def serialized_size(self):
        size = 0
        for name, field in self._field_registry.iteritems():
            size += field.serialized_size()
        return size

    @classmethod
    def minimal_size(cls):
        size = 0
        for name, (_type, default) in cls._fields.iteritems():
            size += _type.minimal_size()
        return size

    def __str__(self):
        return self.serialize().encode("hex").upper()

    def __eq__(self, other):
        return str(self) == str(other)


class BaseField(object):

    def __call__(self, **kwargs):
        ret = copy.copy(self)
        if "initial" in kwargs:
            ret._set_to(kwargs["initial"])
        return ret

#    def __call__(self):
#        return NotImplemented
#    
    def serialize(self):
        return bytearray([])

    def deserialize(self, value, pos):
        return NotImplemented

    @classmethod
    def minimal_size(cls):
        return NotImplemented


class BaseIterable(BaseField, list):

    def __init__(self, initial=[]):
        super(BaseIterable, self).__init__()
        for value in initial:
            self.append(self._type(initial=copy.copy(value)))

    def _set_to(self, values):
        while len(self) > 0:
            self.pop()
        for value in values:
            self.append(value)

    def append(self, value):
        if isinstance(value, self._type):
            new_value = value
        else:
            new_value = self._type(initial=value)
        super(BaseIterable, self).append(new_value)

    def serialize(self):
        ret = bytearray()
        for i in xrange(self.length):
            ret += self[i].serialize()
        return ret

    def deserialize(self, value, pos):
        for i in xrange(self.length):
            self[i] = self._type()
            pos = self[i].deserialize(value, pos)
        return pos

    def __iter__(self):
        for i in xrange(len(self)):
            try:
                yield self[i].value
            except AttributeError:
                yield self[i]


class BaseInt(BaseField):
    """
    Base class for all integer types. Has _signed (bool) and _format (struct format string).
    """

    _length = None
    _signed = None
    _format = ""

    def __init__(self, initial=0):
        self._value = initial

    def _set_to(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = int(value)

    def serialize(self):
        return struct.pack(self._format, self._value)

    def deserialize(self, value, pos):
        self._value = struct.unpack(self._format, value[pos:pos+self.serialized_size()])[0]
        return pos + self.serialized_size()

    @classmethod
    def serialized_size(cls):
        """
        Returns the length of this field in bytes. If the length in bits is not directly
        divisible by 8, an extra byte is added.
        """

        return int(math.ceil(cls._length/8.0))

    def __getattribute__(self, attr):
        if attr in ["__lt__", "__le__", "__eq__", "__ne__", "__gt__", "__ge__",
                "__add__", "__sub__", "__mul__", "__floordiv__", "__mod__",
                "__divmod__", "__pow__", "__lshift__", "__rshift__", "__and__",
                "__xor__", "__or__", "__div__", "__truediv__", "__str__"]:
            return self._value.__getattribute__(attr)
        else:
            return super(BaseInt, self).__getattribute__(attr)

    def __int__(self):
        return self._value

    def __repr__(self):
        return "{} with value {}".format(self.__class__, self._value)

    @classmethod
    def minimal_size(cls):
        return int(math.ceil(cls._length/8.0))


class Length(BaseField):
    """
    A value that defines another field's length.
    """

    def __init__(self, object_type, field_name):
        self._type = object_type()
        self._field = field_name

    def serialized_size(self):
        return self._type.serialized_size()

    def serialize(self, length):  # TODO PyCharm does not like this approach, method signatures don't match
        self._type.value = length
        return self._type.serialize()

    def deserialize(self, value, pos):
        return self._type.deserialize(value, pos)

    def minimal_size(self):
        return self.serialized_size()


class List(BaseIterable):
    """
    An array with its length defined elsewhere.
    """

    def __init__(self, object_type, **kwargs):
        self._type = object_type
        super(List, self).__init__(**kwargs)

    @property
    def length(self):
        return len(self)

    def serialized_size(self):
        return self._type.serialized_size() * self.length

    def deserialize(self, value, pos, length=None):
        if length is None:
            raise IOError("Unknown length.")
        elif length == -1:
            for i in xrange(len(self), (len(value)-pos)/self._type().serialized_size()):
                self.append(0)
            return super(List, self).deserialize(value, pos)
        else:
            for i in xrange(len(self), length):
                self.append(0)
            return super(List, self).deserialize(value, pos)

    def minimal_size(cls):
        return 0


class Array(BaseIterable):
    """
    A fixed-length array of values.
    """

    def __init__(self, object_type, length, **kwargs):
        self._type = object_type
        self._length = length
        super(Array, self).__init__(**kwargs)
        
    @property
    def length(self):
        return self._length

    def serialized_size(self):
        return self._type.serialized_size() * self.length

    def serialize(self):
        dl = self.length - len(self)
        if dl < 0:
            warnings.warn(RuntimeWarning("The number of items in the Array exceeds the length of the array."))
        elif dl > 0:
            self += [self._type() for _ in xrange(dl)]  # TODO is this correct???
        ret = super(Array, self).serialize()
        for i in xrange(dl):
            self.pop(-1)
        return ret

    def deserialize(self, value, pos):
        for i in xrange(len(self), self.length):
            self.append(self._type())
        return super(Array, self).deserialize(value, pos)

    def minimal_size(self):
        return self.serialized_size()

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
    _format = ">L"


class nx_int64(BaseInt):
    _signed = True
    _length = 64
    _format = ">l"


class uint64(BaseInt):
    _signed = False
    _length = 64
    _format = "<L"


class int64(BaseInt):
    _signed = True
    _length = 64
    _format = "<l"
