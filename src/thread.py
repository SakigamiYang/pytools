# coding: utf-8
import threading
import typing
from contextlib import contextmanager

__all__ = ['RWLock']


class RWLock:
    """
    A simple reader-writer lock Several readers can hold the lock simultaneously,
    XOR one writer. Write locks have priority over reads to prevent write starvation.
    """

    def __init__(self) -> None:
        self._rwlock = 0
        self._writers_waiting = 0
        self._monitor = threading.Lock()
        self._readers_ok = threading.Condition(self._monitor)
        self._writers_ok = threading.Condition(self._monitor)

    def acquire_read(self, timeout: typing.Optional[float] = None) -> None:
        """
        Acquire a read lock. Several threads can hold this typeof lock.
        It is exclusive with write locks.
        :param timeout:
            If timeout is not None and timeout >= 0, current thread will wait until timeout passes.
            If the call timeouts and cannot get the lock, will raise RuntimeError
        """
        with self._monitor:
            while self._rwlock < 0 or self._writers_waiting:
                self._readers_ok.wait(timeout)
            self._rwlock += 1

    def acquire_write(self, timeout: typing.Optional[float] = None) -> None:
        """
        Acquire a write lock. Only one thread can hold this lock,
        and only when no read locks are also held.
        :param timeout:
            If timeout is not None and timeout >= 0, current thread will wait until timeout passes.
            If the call timeouts and cannot get the lock, will raise RuntimeError
        """
        with self._monitor:
            while self._rwlock > 0:
                self._writers_waiting += 1
                self._writers_ok.wait(timeout)
                self._writers_waiting -= 1
            self._rwlock = -1

    def promote(self, timeout: typing.Optional[float] = None) -> None:
        """
        Promote an already-acquired read lock to a write lock.
        WARNING: it is very easy to deadlock with this method.
        :param timeout:
            If timeout is not None and timeout >= 0, current thread will wait until timeout passes.
            If the call timeouts and cannot get the lock, will raise RuntimeError
        """
        with self._monitor:
            self._rwlock -= 1
            while self._rwlock > 0:
                self._writers_waiting += 1
                self._writers_ok.wait(timeout)
                self._writers_waiting -= 1
            self._rwlock = -1

    def demote(self) -> None:
        """Demote an already-acquired write lock to a read lock."""
        with self._monitor:
            self._rwlock = 1
            self._readers_ok.notify_all()

    def release(self) -> None:
        """Release a lock, whether read or write."""
        with self._monitor:
            if self._rwlock < 0:
                self._rwlock = 0
            else:
                self._rwlock -= 1
            wake_writers = self._writers_waiting and self._rwlock == 0
            wake_readers = self._writers_waiting == 0
        if wake_writers:
            with self._writers_ok:
                self._writers_ok.notify()
        elif wake_readers:
            with self._readers_ok:
                self._readers_ok.notify_all()

    @contextmanager
    def lock_read(self, timeout: typing.Optional[float] = None) -> None:
        """This method is designed to be used via the `with` statement."""
        try:
            self.acquire_read(timeout)
            yield
        finally:
            self.release()

    @contextmanager
    def lock_write(self, timeout: typing.Optional[float] = None) -> None:
        """This method is designed to be used via the `with` statement."""
        try:
            self.acquire_write(timeout)
            yield
        finally:
            self.release()
