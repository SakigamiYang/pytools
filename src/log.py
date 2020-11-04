# coding: utf-8
import typing
from datetime import timedelta
from functools import wraps
from time import time

from loguru import logger

__all__ = ['logger', 'sink_logfile', 'trace']


def sink_logfile(prefix: str, level: str = 'INFO', retention: timedelta = timedelta(days=7)) -> int:
    """
    Set file sinking for logger.
    :param prefix: file path prefix, the name of log files will be set to 'prefix-YYYYMMDD.log'
    :param level: log level, TRACE < DEBUG < INFO < SUCCESS < WARNING < ERROR < CRITICAL
    :param retention:
    :return:
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
                      rotation='1 day',
                      retention=retention,
                      compression='gz',
                      encoding='utf-8')


def trace(fn: typing.Callable,
          enter_msg: typing.Optional[str] = None,
          leave_msg: typing.Optional[str] = None,
          used_time_precision: int = 3):
    """
    Decorator for print tracing log.
    :param fn: function
    :param enter_msg: msg to print out when entering the function
    :param leave_msg: msg to print out when leaving the function
    :param used_time_precision: round used time to n digits
    :return: result of function
    """
    fn_name = fn.__name__
    enter_msg = enter_msg or 'enter'
    leave_msg = leave_msg or 'leave'

    @wraps(fn)
    def wrapper(*args, **kwargs) -> typing.Any:
        logger.info(f'[{fn_name}] {enter_msg}')
        now = time()
        result = fn(*args, **kwargs)
        then = time()
        logger.info(f'used time: {round(then - now, used_time_precision)}s')
        logger.info(f'[{fn_name}] {leave_msg}')
        return result

    return wrapper
