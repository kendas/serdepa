from collections import OrderedDict
from functools import reduce

from six import BytesIO

from .primitives import nx_uint8
from .exceptions import DeserializeError, PacketDefinitionError, ValidationError
from .base import BaseField, MetaSerdepa
from .singletons import DEFAULT, DEFERRED


class BaseIterable(BaseField):
    """
    A base class for iterable fields.

    An iterable field has the following properties:
        - it has a value type (a serdepa field)
        - it can be iterated over
        - it can be assigned to via indexing
        - it can be fetched from via indexing
    """
    _container = NotImplemented

    def __init__(self, object_type):
        super(BaseIterable, self).__init__()
        self._field_values = OrderedDict()
        # Force self._type to be a class
        if isinstance(object_type, MetaSerdepa):
            self._type = object_type
        else:
            self._type = object_type.__class__

    def from_bytes(self, buffer, parent):
        for i, item in enumerate(self._container):
            buffer_empty = item.from_bytes(buffer, self)
            if buffer_empty and i < len(self) - 1:
                raise DeserializeError("Input too short")

    def to_bytes(self, parent):
        output = BytesIO()
        for item in self._container:
            output.write(item.to_bytes(self))
        return output.getvalue()

    def _set_item(self, index, value):
        self._container[index].__set__(self, value)

    def _get_item(self, index):
        return self._container[index].__get__(self, self.__class__)

    def _get_slice(self, slice_):
        return [field.__get__(self, self.__class__) for field in self._container[slice_]]

    def _get_value(self, parent):
        return parent._field_values[self._init_order]

    def _set_value(self, parent, value):
        raise NotImplementedError()

    def __len__(self):
        return len(self._container)

    def __eq__(self, other):
        return other == [self._get_item(i) for i in range(len(self._container))]

    def __iter__(self):
        return (self._get_item(i) for i in range(len(self._container)))

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._get_slice(item)
        else:
            return self._get_item(item)

    def __setitem__(self, key, value):
        raise NotImplementedError()


class Array(BaseIterable):
    """
    A fixed-length array of values.
    """

    def __init__(self, object_type, length, default=DEFAULT):
        super(Array, self).__init__(object_type)
        self._length = length

        self._container = []
        for _ in range(length):
            instance = self._type()
            self._container.append(instance)
            instance.__set__(self, DEFAULT)
        if default is not DEFAULT:
            if len(default) != length:
                raise PacketDefinitionError(
                    "The length of the default must equal the length of {}".format(self.__class__.__name__)
                )
            for i, value in enumerate(default):
                instance = self._container[i]
                instance.__set__(self, value)

    @property
    def length(self):
        return self._length

    def __len__(self):
        return self.length

    def _validate_length(self, value):
        if len(value) != self.length:
            raise ValidationError("The value {} is of invalid length for {}".format(value, self.__class__.__name__))

    @property
    def _validators(self):
        return [self._validate_length]

    def __get__(self, instance, owner):
        return self._get_value(instance)

    def __set__(self, instance, value):
        if value is DEFAULT:
            value = [0 for _ in range(self.length)]
        self._set_value(instance, value)

    def _set_value(self, parent, value):
        self.validate(value)
        for i, item in enumerate(value):
            self._get_value(parent)._set_item(i, item)

    def __setitem__(self, key, value):
        if -self.length - 1 < key < self.length:
            self._set_item(key, value)
        else:
            raise IndexError("The array has a length of {}. Can't assign to index {}".format(
                self.length, key
            ))

    def __repr__(self):
        return "Array({}, {}, {})".format(self.length, self._type.__name__, list(self))


class List(BaseIterable):
    """
    An array with its length defined elsewhere.
    """

    def __init__(self, object_type, default=DEFAULT):
        """
        :type default: list | None
        """
        super(List, self).__init__(object_type)

        if default is DEFAULT:
            default = []
        self._container = []
        self.extend(default)
        self._length = None

    def from_bytes(self, buffer, parent):
        if self is parent._tail_list:
            buffer_empty = buffer.tell() >= len(buffer.getvalue())
            while not buffer_empty:
                self.append(DEFAULT)
                buffer_empty = self._container[-1].from_bytes(buffer, self)
            return buffer_empty
        else:
            pass
        # for i, item in enumerate(self._container):
        #     buffer_empty = item.from_bytes(buffer, self)
        #     if buffer_empty and i < len(self) - 1:
        #         raise DeserializeError("Input too short")

    def _set_value(self, parent, value):
        field = self._get_value(parent)
        if value is DEFAULT:
            value = []
        for _ in range(field.length):
            field.pop()
        field.extend(value)

    def __get__(self, instance, owner):
        return self._get_value(instance)

    def __set__(self, instance, value):
        self._set_value(instance, value)

    def __setitem__(self, key, value):
        self._set_item(key, value)

    def __repr__(self):
        return "List({}, {})".format(self._type.__name__, list(self))

    def _del_item(self, index):
        field = self._container.pop(index)
        self._field_values.pop(field._init_order)

    @property
    def length(self):
        return len(self)

    def __len__(self):
        return len(self._container)

    def append(self, value):
        instance = self._type()
        self._container.append(instance)
        instance.__set__(self, value)

    def extend(self, value):
        for item in value:
            self.append(item)

    def pop(self, index=-1):
        value = self._get_item(index)
        self._del_item(index)
        return value


class Length(BaseField):
    """
    A value that defines another field's length.
    """

    def __init__(self, object_type, field_name, default=DEFAULT):
        # Force self._type to be an instance
        if isinstance(object_type, MetaSerdepa):
            self._type = object_type(default=default)
        elif isinstance(object_type, BaseField):
            if default is not DEFAULT:
                raise PacketDefinitionError(
                    "The default argument is supported for un-instantiated SerdepaFields on {}".format(
                        self.__class__.__name__
                    )
                )
            self._type = object_type._copy()
        else:
            raise PacketDefinitionError("The value type of {} must be a BaseField".format(self.__class__.__name__))
        self._field_name = field_name
        self._list = None
        super(Length, self).__init__()

    def to_bytes(self, parent):
        return self._type.to_bytes(self)

    def from_bytes(self, buffer, parent):
        return self._type.from_bytes(buffer, self)

    def __get__(self, instance, own5er):
        return self._type

    def __set__(self, instance, value):
        self._type = value


class ByteString(BaseField):
    """
    A variable or fixed-length string of bytes.
    """

    def __init__(self, length=None):
        if length is not None:
            self._data_container = Array(nx_uint8, length)
        else:
            self._data_container = List(nx_uint8)
        super(ByteString, self).__init__()

    def __getattr__(self, attr):
        if attr not in ['_data_container']:
            return getattr(self._data_container, attr)
        else:
            return super(ByteString, self).__getattribute__(attr)

    def __setattr__(self, attr, value):
        if attr not in ['_data_container', '_value']:
            setattr(self._data_container, attr, value)
        else:
            super(ByteString, self).__setattr__(attr, value)

    @property
    def _value(self):
        return reduce(
            lambda x, v: x + (v[1] << (8*v[0])),
            enumerate(
                reversed(list(self._data_container))
            ),
            0
        )

    def __eq__(self, other):
        return self._value == other

    def __repr__(self):
        return "{} with value {}".format(self.__class__, self._value)

    def __str__(self):
        return "{value:0{size}X}".format(
            value=self._value,
            size=self._data_container.serialized_size()*2,
        )

    def __len__(self):
        return len(self._data_container)
