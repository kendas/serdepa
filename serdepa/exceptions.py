class SerdepaError(Exception):
    """
    Base error for the serdepa package.
    """
    pass


class PacketDefinitionError(SerdepaError):
    """
    Error that is raised when a packet definition is malformed in some way.
    """
    pass


class DeserializeError(SerdepaError):
    """
    Error that is raised when deserialization fails.
    """
    pass


class ValidationError(SerdepaError):
    """
    Error that is raised when assigning a value to a parameter fails.
    """
    pass
