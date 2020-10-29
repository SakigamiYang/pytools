import threading
import typing
from enum import Enum, auto

__all__ = ['RWLock', 'LockType']


class LockType(Enum):
    R_LOCK = auto()
    W_LOCK = auto()


class RWLock:
    """
    Read Write Lock is a typical lock type in computer world.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._nb_read = 0
        self._nb_write = 0

    def acquire_write_lock(self, wait_time: typing.Optional[float] = None) -> None:
        """
        Acquire write lock.
        :param wait_time:
            If wait_time is not None and wait_time >= 0, current thread will wait until wait_time passes.
            If the call timeouts and cannot get the lock, will raise RuntimeError
        """

        with self._cond:
            if self._nb_write > 0 or self._nb_read > 0:
                self._cond.wait(wait_time)
            self._nb_write += 1

    def release_write_lock(self) -> None:
        """
        Release write lock.
        """

        with self._cond:
            self._nb_write -= 1
            if self._nb_write == 0:
                self._cond.notify_all()

    def acquire_read_lock(self, wait_time: typing.Optional[float] = None) -> None:
        """
        Acquire read lock.
        :param wait_time:
            If wait_time is not None and wait_time >= 0, current thread will wait until wait_time passes.
            If the call timeouts and cannot get the lock, will raise RuntimeError
        """

        with self._cond:
            if self._nb_write > 0:
                self._cond.wait(wait_time)
            self._nb_read += 1

    def release_read_lock(self) -> None:
        """
        Release read lock.
        """

        with self._cond:
            self._nb_read -= 1
            if self._nb_read == 0 and self._nb_write == 0:
                self._cond.notify()
