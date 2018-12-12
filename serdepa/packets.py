from collections import OrderedDict
from codecs import encode

from six import add_metaclass, BytesIO

from .base import MetaSerdepa, BaseField
from .containers import List, Length, BaseIterable
from .exceptions import PacketDefinitionError, ValidationError, DeserializeError
from .singletons import DEFAULT


class PacketBase(BaseField):
    """
    A placeholder for metaclass purposes. DO NOT INHERIT FROM THIS.
    """
    pass


class MetaSerdepaPacket(MetaSerdepa):
    """
    Metaclass of SerdepaPackets. Handles the magic that is needed for the various fields.
    """
    def __new__(mcs, what, bases, attrs):
        fields = {}

        for name, field in attrs.items():
            if isinstance(field, MetaSerdepa):
                raise PacketDefinitionError(
                    "The field {} is not instantiated on {}".format(name, mcs.__name__)
                )
            if isinstance(field, BaseField):
                fields[name] = field

        attrs["_fields"] = OrderedDict(
            (name, field)
            for name, field in sorted(fields.items(), key=lambda x: x[1]._init_order)
        )

        return super(MetaSerdepa, mcs).__new__(mcs, what, bases, attrs)


@add_metaclass(MetaSerdepaPacket)
class SerdepaPacket(PacketBase):
    """
    The superclass for any packets.

    A packets has the following properties:
        - it can be serialized (serialize)
        - it can be constructed by deserializing a bytestring
        - it can be assigned as a field
        - it has fields
    :type _fields: dict[str, BaseField]
    :type _field_values dict[BaseField]
    """

    def __init__(self, default=DEFAULT, **kwargs):
        """
        Constructs a new packet. New packets can have default values for their
        fields assigned in the following ways:
            - Passing in a pre-existing instance of the packet
            - Passing in some (or all) of the field values by name using keyword
              arguments
        :param SerdepaPacket default: The default values for this packet's
                fields will be copied from this packet
        :param kwargs: The default values for the fields by name
        """

        super(SerdepaPacket, self).__init__()
        if default is not DEFAULT and not isinstance(default, type(self)):
            raise PacketDefinitionError(
                "The default values for a {0} can "
                "only come from another {0} instance.".format(self)
            )
        self._args = (default,)
        self._kwargs = kwargs
        self._field_values = OrderedDict()
        list_to_length = OrderedDict()
        for name, field in self._fields.items():
            if default is not DEFAULT:
                field_default = getattr(default, name)
                if name in kwargs:
                    raise PacketDefinitionError("'default' and field defaults are mutually exclusive.")
            else:
                field_default = kwargs.pop(name, DEFAULT)

            # These are complex types and must therefore be stored on the instance, not as
            # class attributes
            if isinstance(field, (SerdepaPacket, BaseIterable, Length)):
                self._field_values[field._init_order] = field._copy()

            # Detect List and Length fields
            if isinstance(field, Length):
                if field._field_name not in self._fields:
                    raise PacketDefinitionError("No List field by the name {}".format(field._field_name))
                # Also, validate that the field the Length is referring to, is actually a List
                elif not isinstance(self._fields[field._field_name], List):
                    raise PacketDefinitionError("The field {} is not a List".format(field._field_name))
                else:
                    list_to_length[field._field_name] = name
            elif isinstance(field, List):
                if name not in list_to_length:
                    list_to_length[name] = None
                self._field_values[field._init_order] = field._copy()

            # Finally, set the calculated default value for the field
            setattr(self, name, field_default)

        if kwargs:
            raise PacketDefinitionError("Unknown fields {} for {}".format(
                tuple(kwargs.keys()), self.__class__.__name__
            ))

        # Create references between the List and Length instances
        for i, item in enumerate(reversed(list_to_length.items())):
            list_, length = item
            if i != 0 and length is None:
                raise PacketDefinitionError(
                    "The List {} is not the last field, but its length is unknown.".format(list_)
                )
            # list_ must truly be the last field.
            elif list(reversed(self._fields))[0] != list_:
                raise PacketDefinitionError(
                    "The List {} is not the last field, but its length is unknown.".format(list_)
                )
            if length is not None:
                self._fields[list_]._length = self._fields[length]
                self._fields[length]._list = self._fields[list_]

    def resolve_attribute(self, path):
        parts = path.split('.', maxsplit=1)
        if len(parts) > 1:
            return getattr(self, parts[0]).resolve_attribute(parts[1])
        else:
            return getattr(self, parts[0])

    def __get__(self, instance, owner):
        if issubclass(owner, SerdepaPacket):
            return self._get_value(instance)
        else:
            return self

    def __set__(self, instance, value):
        if isinstance(instance, SerdepaPacket):
            # If the parent is a SerdepaPacket, the values are stored
            # in another instance of this packet, stored in the dict
            # _field_values
            instance = self._get_value(instance)
        self._set_value(instance, value)

    def _get_value(self, parent):
        return parent._field_values[self._init_order]

    def _set_value(self, parent, value):
        if value is DEFAULT:
            value = self._default
        self.validate(value)
        for name in self._fields:
            setattr(parent, name, getattr(value, name))

    def serialize(self):
        output = BytesIO()
        for name, field in self._fields.items():
            output.write(self._fields[name].to_bytes(self))
        return output.getvalue()

    @property
    def _tail_list(self):
        """
        Fetches the last field if it is a list, otherwise None
        :return: List | None
        """
        try:
            last = getattr(self, list(reversed(self._fields))[0])
        except IndexError:
            return None
        else:
            return self._field_values[last._init_order] if isinstance(last, List) else None

    @classmethod
    def deserialize(cls, data, *args, **kwargs):
        instance = cls(*args, **kwargs)
        buffer = BytesIO(data)
        buffer.seek(0)

        instance.from_bytes(buffer, None)
        return instance

    def __str__(self):
        return encode(self.serialize(), "hex").decode().upper()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.serialize() == other.serialize()

    def to_bytes(self, parent):
        return self.serialize()

    def from_bytes(self, buffer, parent):
        # This is done so the `buffer_empty` check does not fail on packets with
        # no tail.
        buffer_empty = len(buffer.getvalue()) == 0
        #print(self._field_values)
        for name, field in self._fields.items():
            if isinstance(field, (SerdepaPacket, BaseIterable)):
                field = self._field_values[field._init_order]
            if buffer_empty and not (field is self._tail_list and self._parent is None):
                raise DeserializeError("Input too short")
            buffer_empty = field.from_bytes(buffer, self)
        return buffer_empty

    @classmethod
    def _validate_class(cls, value):
        if not isinstance(value, cls):
            raise ValidationError("Invalid type value {} for {}".format(value, cls.__name__))

    @property
    def _validators(self):
        return [self._validate_class]

    @property
    def _default(self):
        return self.__class__(*self._args, **self._kwargs)

    def __hash__(self):
        return super(SerdepaPacket, self).__hash__()
