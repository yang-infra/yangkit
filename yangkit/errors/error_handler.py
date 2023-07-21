import contextlib
from yangkit.errors import YModelError


@contextlib.contextmanager
def handle_type_error():
    """
    Rethrow TypeError as YModelError
    """
    _exc = None
    try:
        yield
    except TypeError as err:
        _exc = YModelError(str(err))
    finally:
        if _exc:
            raise _exc
