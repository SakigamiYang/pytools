import typing

__all__ = ['BaseError', 'CacheFullError']


class BaseError(Exception):
    """
    Base exception. All other exceptions will inherit it.
    """

    def __init__(self, msg: typing.Any) -> None:
        self._msg = f'pytools module exception: {msg}'

    def __repr__(self) -> str:
        return repr(self._msg)

    def __str__(self) -> str:
        return self._msg


class CacheFullError(BaseError):
    def __init__(self, msg: typing.Any) -> None:
        super().__init__(msg)
