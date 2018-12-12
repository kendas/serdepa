"""
base.py: Binary packet serialization and deserialization library.
"""

from __future__ import unicode_literals

from copy import copy

from six import add_metaclass


__author__ = "Raido Pahtma, Kaarel Ratas"
__license__ = "MIT"


class MetaSerdepa(type):
    """
    Metaclass of all serdepa objects - allows for the counting of instantiation order.
    """
    _counter = 0


@add_metaclass(MetaSerdepa)
class BaseField(object):
    """
    The base class for serdepa fields - that is to say any value, that can be assigned as
    a field to a packet. This includes other packets. So everything, essentially.

    A field has the following properties:
        - it has an internal value
        - its internal value can be turned into some number of bytes (to_bytes)
        - its internal value can be derived from some number of bytes (from_bytes)
        - it can be assigned as a field, which means:
            - its internal value can be set (this is validated)
            - its internal value can be fetched and used as a normal Python value
    """
    _validators = []
    _default = NotImplemented

    #def __new__(cls, *args, **kwargs):
    #    instance = super(BaseField, cls).__new__(cls)
    #    # Set the _copy function here so subclasses can restrict sending arguments
    #    # all the way down the chain
    #    instance._args = args
    #    instance._kwargs = kwargs
    #    return instance

    def validate(self, value):
        for validator in self._validators:
            validator(value)

    def __init__(self):

        self._init_order = MetaSerdepa._counter
        MetaSerdepa._counter += 1

#    def __hash__(self):
#        return self._init_order
#
    def __get__(self, instance, owner):
        """
        The property getter invoked when this object is accessed on a serdepa
        packet.
        :return:
        """
        raise NotImplementedError("__get__ is not implemented on {}".format(self.__class__.__name__))

    def __set__(self, instance, value):
        """
        The property setter invoked when this object is set on a serdepa
        packet. `_setter = None` means setting this object directly is illegal.
        :param value:
        :raises: serdepa.exceptions.ValidationError
        """
        raise NotImplementedError("__set__ is not implemented on {}".format(self.__class__.__name__))

    def from_bytes(self, buffer, parent):
        raise NotImplementedError("from_bytes is not implemented on {}".format(self.__class__.__name__))

    def to_bytes(self, parent):
        raise NotImplementedError("to_bytes is not implemented on {}".format(self.__class__.__name__))

    def _copy(self):
        return copy(self)
