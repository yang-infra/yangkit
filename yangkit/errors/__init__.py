
class YError(Exception):
    """
    Base class for Y Errors.
    The subclasses give a specialized view of the error that has occurred.
    """

    def __init__(self, error_msg):
        self.message = error_msg

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.__repr__()


class YInvalidArgumentError(YError):
    """
    Invalid Argument(s) provided
    Use the error_msg for the error.
    """
    pass


class YModelError(YError):
    """
    Thrown when a model constraint is violated.
    """
    pass


class YCodecError(YError):
    """
    Exception for Service Side Validation
    """
    pass
