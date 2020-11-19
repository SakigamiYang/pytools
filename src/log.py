# coding: utf-8
import typing
from datetime import timedelta
from functools import wraps
from time import time

from loguru import logger

__all__ = ['logger', 'sink_logfile', 'trace', 'LogLevel']


class LogLevel:
    __slots__ = ()
    TRACE = 'TRACE'
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    SUCCESS = 'SUCCESS'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


def sink_logfile(prefix: str, level: str = LogLevel.INFO, retention: int = 30) -> int:
    """
    Set file sinking for logger.
    :param prefix: file path prefix, the name of log files will be set to 'prefix-YYYYMMDD.log'
    :param level: log level, TRACE < DEBUG < INFO < SUCCESS < WARNING < ERROR < CRITICAL
    :param retention: the number of log files to keep
    :return: an identifier associated with the added sink and which should be used to remove it
    """
    return logger.add(sink=prefix + '-{time:YYYYMMDD}.log',
                      level=level,
                      format=('{time:YYYY-MM-DD HH:mm:ss.SSS}'
                              ' | {level: <8}'
                              ' | p{process}'
                              ' | {file}'
                              ':{function}'
                              ':{line}'
                              ' - {message}'),
                      colorize=False,
                      rotation=timedelta(days=1),
                      retention=retention,
                      compression='gz',
                      encoding='utf-8')


# noinspection PyPep8Naming
class trace:
    """Decorator for print tracing log."""

    def __init__(self,
                 enter_msg: str = 'entering',
                 leave_msg: str = 'leaving',
                 used_time_precision: int = 3) -> None:
        """
        Initializer.
        :param enter_msg: msg to print out when entering the function, 'entering' as default
        :param leave_msg: msg to print out when leaving the function, 'leaving' as default
        :param used_time_precision: round used time to n digits, 3 (milliseconds) as default
        """
        self._enter_msg = enter_msg or 'entering'
        self._leave_msg = leave_msg or 'leaving'
        self._used_time_precision = used_time_precision

    def __call__(self, fn: typing.Callable) -> typing.Any:
        """
        Tracing.
        :param fn: the function to trace
        :return: result of the function
        """

        fn_name = fn.__name__

        @wraps(fn)
        def _wrapper(*args, **kwargs) -> typing.Any:
            logger.info(f'[{fn_name}] {self._enter_msg}')
            now = time()
            result = fn(*args, **kwargs)
            then = time()
            logger.info(f'used time: {round(then - now, self._used_time_precision)}s')
            logger.info(f'[{fn_name}] {self._leave_msg}')
            return result

        return _wrapper
