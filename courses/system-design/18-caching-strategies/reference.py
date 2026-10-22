"""Caching strategies: eviction policies, read and write patterns, and
stampede protection."""

import itertools
import math
import threading
from collections import OrderedDict


# --- 1. Eviction -------------------------------------------------------------


class LRUCache:
    """Evicts the least recently used key. (Provided: you built one in lesson 3.)"""

    def __init__(self, capacity):
        self.capacity = capacity
        self.items = OrderedDict()

    def get(self, key):
        if key not in self.items:
            return None
        self.items.move_to_end(key)
        return self.items[key]

    def put(self, key, value):
        self.items[key] = value
        self.items.move_to_end(key)
        if len(self.items) > self.capacity:
            self.items.popitem(last=False)


class LFUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = {}  # key -> [value, uses, last use]
        self._clock = itertools.count()

    def get(self, key):
        item = self.items.get(key)
        if item is None:
            return None
        item[1] += 1
        item[2] = next(self._clock)
        return item[0]

    def put(self, key, value):
        if key in self.items:
            item = self.items[key]
            item[0] = value
            item[1] += 1
            item[2] = next(self._clock)
            return
        if len(self.items) >= self.capacity:
            victim = min(self.items, key=lambda k: (self.items[k][1], self.items[k][2]))
            del self.items[victim]
        self.items[key] = [value, 1, next(self._clock)]


# --- 2. Read and write patterns ---------------------------------------------


class CacheAside:
    def __init__(self, cache, db):
        self.cache = cache
        self.db = db

    def read(self, key):
        value = self.cache.get(key)
        if value is None:
            value = self.db.get(key)
            if value is not None:
                self.cache.set(key, value)
        return value

    def write(self, key, value):
        self.db.set(key, value)
        self.cache.delete(key)  # invalidate; the next read loads the new value


class WriteThrough(CacheAside):
    def write(self, key, value):
        self.db.set(key, value)
        self.cache.set(key, value)


class WriteBehind(CacheAside):
    def __init__(self, cache, db):
        super().__init__(cache, db)
        self.pending = {}  # key -> latest value not yet in the database

    def read(self, key):
        if key in self.pending:
            return self.pending[key]
        return super().read(key)

    def write(self, key, value):
        self.pending[key] = value
        self.cache.set(key, value)

    def flush(self):
        for key, value in self.pending.items():
            self.db.set(key, value)
        self.pending.clear()


# --- 3. Stampedes ------------------------------------------------------------


class SingleFlight:
    """Runs one call per key at a time; concurrent callers share its result."""

    def __init__(self):
        self.lock = threading.Lock()
        self.calls = {}  # key -> (done event, result holder)

    def do(self, key, fn):
        with self.lock:
            call = self.calls.get(key)
            leader = call is None
            if leader:
                call = (threading.Event(), {})
                self.calls[key] = call
        done, result = call
        if leader:
            try:
                result["value"] = fn()
            except Exception as e:
                result["error"] = e
            finally:
                with self.lock:
                    del self.calls[key]
                done.set()
        else:
            done.wait()
        if "error" in result:
            raise result["error"]
        return result["value"]


class CoalescingCache:
    def __init__(self, loader, ttl, clock):
        self.loader = loader
        self.ttl = ttl
        self.clock = clock
        self.entries = {}  # key -> (value, expires at)
        self.flight = SingleFlight()

    def get(self, key):
        entry = self.entries.get(key)
        if entry and self.clock() < entry[1]:
            return entry[0]

        def load():
            value = self.loader(key)
            self.entries[key] = (value, self.clock() + self.ttl)
            return value

        return self.flight.do(key, load)


def jittered_ttl(ttl, rng, spread=0.1):
    return ttl * (1 + rng.uniform(-spread, spread))


def should_refresh_early(now, expiry, delta, beta, rand):
    return now - delta * beta * math.log(rand) >= expiry
