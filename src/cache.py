# coding: utf-8
import logging
import queue
import typing
from contextlib import contextmanager
from time import time
from uuid import uuid4

from errors import CacheFullError
from thread import RWLock, LockType

__all__ = ['CacheFullError', 'KVCache', 'KvCache']


class KVCache:
    """
    Key-Value cache.

    You can use function set/get to access the cache.

    When a k-v is hit by function get,
    the expire time of this key will be expanded.
    """

    INFINITE_TIME_SEC = 10000 * 365 * 24 * 60 * 60  # 10000 years, enough for cache
    TIME_EXTENSION_SEC = 5 * 60  # 5 minutes

    def __init__(self,
                 name: typing.Optional[str] = None,
                 maxsize: int = 0,
                 time_extension_sec: typing.Optional[float] = None) -> None:
        """
        Initializer.
        :param name: name
        :param maxsize:
            0 by default which means store as more cache k/v as the system can
        :param time_extension_sec:
            When a cache item has been hit, the expire_time will be refreshed
            to the greater one, either (TIME_EXTENSION + time.time()) or
            (TIME_EXTENSION + expire_sec)
        """

        if name is None:
            logging.warning('You initialize the KVCache with no name. '
                            'Strongly suggest you pick up a meaningful name for it in order to debug.')
        if time_extension_sec is not None and time_extension_sec <= 0:
            raise ValueError("'time_extension_sec' should > 0")

        self._name = name or f'cache.unnamed.{uuid4().hex}'
        self._maxsize = maxsize
        self._time_extension = time_extension_sec or KVCache.TIME_EXTENSION_SEC
        self._sorted_keys = queue.PriorityQueue(maxsize=self._maxsize)
        self._kv_data = dict()
        self._lock = RWLock()

    @contextmanager
    def _release_lock(self, lock_type: LockType) -> None:
        if lock_type == LockType.R_LOCK:
            self._lock.acquire_read_lock()
        else:
            self._lock.acquire_write_lock()
        try:
            yield
        except Exception as e:
            logging.warning(f'some error happened in cache: {e}')
        finally:
            if lock_type == LockType.R_LOCK:
                self._lock.release_read_lock()
            else:
                self._lock.release_write_lock()

    def set(self, kvdict: typing.Mapping, expire_sec: typing.Optional[float] = None) -> bool:
        """
        Set cache with k-v dict.
        :param kvdict: a dict that contains your cached object
        :param expire_sec: expire time, if None, the cache will never expire
        :return: True if set cache successfully, False otherwise
        """

        if self._maxsize != 0 and len(kvdict) > self._maxsize:
            logging.error(f'KVCache {self._name} cannot insert more elements than the maxsize')
            return False

        expire_value = expire_sec + time() \
            if expire_sec is not None and expire_sec < self.INFINITE_TIME_SEC \
            else self.INFINITE_TIME_SEC
        with self._release_lock(LockType.W_LOCK):
            for k, v in kvdict.items():
                if k in self._kv_data:
                    logging.debug(f'KVCache: Key:{k} updated.')
                    self._kv_data[k] = (expire_value, v)
                else:
                    if not self._heapq_newset(k, v, expire_value):
                        return False
        return True

    def _heapq_newset(self, key: typing.Any, value: typing.Any, expire_value: float) -> bool:
        # No limit, put key into the queue
        if self._maxsize == 0 or len(self._kv_data) < self._maxsize:
            self._sorted_keys.put(expire_value, key)
            self._kv_data[key] = (expire_value, value)
            return True

        # Need replace the smallest one
        while True:
            try:
                pop_value = self._sorted_keys.get_nowait()
            except queue.Empty:
                return False
            real_value = self._kv_data.get(pop_value[1], None)
            if real_value is None:
                self._kv_data[key] = (expire_value, value)
                self._sorted_keys.put((expire_value, key))
                return True
            if real_value[0] > pop_value[0]:
                # resort, adjust real
                self._sorted_keys.put((expire_value, key))
            else:
                if expire_value < pop_value[0]:
                    logging.error(f'KVCache {self._name} the alorithm you design has faults. '
                                  f'The new inserted cache {(key, expire_value)} expire time '
                                  f'< the oldest cache {pop_value} in it')
                    return False
                del self._kv_data[pop_value[1]]
                self._kv_data[key] = (expire_value, value)
                self._sorted_keys.put((expire_value, key))
                break
        return True

    def _get_refreshed_expire_time(self, expire_value: float) -> float:
        new_refresh = time() + self._time_extension
        new_expire = expire_value + self._time_extension
        return new_expire if new_expire < new_refresh else new_refresh

    def get(self, key: typing.Any) -> typing.Any:
        """
        Get cached value with key.
        If the cache is expired, it will return None.
        If the key does not exist, it will return None.
        :param key: key
        :return: cached value
        """

        with self._release_lock(LockType.R_LOCK):
            if key not in self._kv_data:
                return None
            expire_value, value = self._kv_data[key]
            if time() > expire_value:
                logging.info(f'KVCache {self._name}: key {key} hit, but exipred')
                del self._kv_data[key]
                return None
            logging.debug(f'key:{key} of KVCached fetched')
            expire_value = self._get_refreshed_expire_time(expire_value)
            self._kv_data[key] = (expire_value, value)
            return value

    def pop_n_expired(self, num: int = 0) -> typing.Mapping:
        """
        Pop N expired value.
        :param num: if num is 0, will get all expired key-values
        :return: expired items
        """

        result = dict()
        now = time()
        all_expired = num == 0
        with self._release_lock(LockType.R_LOCK):
            while True:
                try:
                    pop_value = self._sorted_keys.get_nowait()
                except queue.Empty:
                    break
                real_value = self._kv_data.get(pop_value[1], None)
                if real_value is None:
                    continue
                if real_value[0] > pop_value[0]:
                    self._sorted_keys.put((real_value[0], pop_value[1]))
                else:
                    if real_value[0] > now:
                        break
                    else:
                        result[pop_value[1]] = real_value
                        del self._kv_data[pop_value[1]]
                        if not all_expired:
                            num -= 1
                if not all_expired and num <= 0:
                    break
        return result

    def __len__(self) -> int:
        return len(self._kv_data)

    def clear(self) -> None:
        """
        Clear all cache.
        """
        with self._release_lock(LockType.W_LOCK):
            del self._kv_data
            self._kv_data = dict()
            del self._sorted_keys
            self._sorted_keys = queue.PriorityQueue(self._maxsize)


# for compatibility
KvCache = KVCache
