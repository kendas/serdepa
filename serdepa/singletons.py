class Default(object):
    """
    A special value to signify the default value for various fields.
    """
    def __repr__(self):
        return '<Default value>'

    def __str__(self):
        return '<Default value>'


class Deferred(object):
    """
    A special value to signify the fact that a field's value is deferred.
    """
    def __repr__(self):
        return '<Deferred value>'

    def __str__(self):
        return '<Deferred value>'


DEFAULT = Default()
DEFERRED = Deferred()
