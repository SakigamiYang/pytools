import typing
from functools import wraps
from time import time

__all__ = ['TraceUsedTime']


class TraceUsedTime:
    """
    Trace used time inside a function.
    example:
        @decorators.TraceUsedTime(logging.info)
        def test():
            print('test')
            time.sleep(4)
    """

    def __init__(self, logging_func: typing.Callable = print, enter_msg: str = '', leave_msg: str = '') -> None:
        """
        Initialize decorator.
        :param logging_func: logging function that accept one parameter
        :param enter_msg: message to output when entering the function
        :param leave_msg: message to output when leaving the function
        """
        self._logging_func = logging_func
        self._enter_msg = enter_msg
        self._leave_msg = leave_msg

    def __call__(self, func: typing.Callable) -> typing.Callable:
        @wraps(func)
        def _wrapper_func(*args, **kwargs):
            now = time()
            self._logging_func(f'enter function: {func}, msg: {self._enter_msg}')
            result = func(*args, **kwargs)
            then = time()
            used_time = then - now
            self._logging_func(f'leave function: {func}, msg: {self._leave_msg}, used_time: {used_time}')
            return result

        return _wrapper_func
