"""Caching strategies: eviction policies, read and write patterns, and
stampede protection.

Three parts. The lesson describes each one; the tests check them separately.
"""

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
    """Evicts the least frequently used key; ties go to the least recently
    used. get and put both count as a use."""

    def __init__(self, capacity):
        self.capacity = capacity

    def get(self, key):
        """The value, or None if key isn't cached."""
        raise NotImplementedError

    def put(self, key, value):
        raise NotImplementedError


# --- 2. Read and write patterns ---------------------------------------------
#
# cache has get(key) (None on a miss), set(key, value), and delete(key).
# db has get(key) (None if missing) and set(key, value).


class CacheAside:
    def __init__(self, cache, db):
        self.cache = cache
        self.db = db

    def read(self, key):
        """Try the cache; on a miss, load from the database and fill the cache."""
        raise NotImplementedError

    def write(self, key, value):
        """Write the database, then invalidate the cached copy."""
        raise NotImplementedError


class WriteThrough(CacheAside):
    def write(self, key, value):
        """Write the database and the cache together."""
        raise NotImplementedError


class WriteBehind(CacheAside):
    def write(self, key, value):
        """Write the cache now and the database later, in flush()."""
        raise NotImplementedError

    def flush(self):
        """Write each changed key's latest value to the database once."""
        raise NotImplementedError


# --- 3. Stampedes ------------------------------------------------------------


class SingleFlight:
    """Runs one call per key at a time; concurrent callers share its result."""

    def do(self, key, fn):
        return fn()


class CoalescingCache:
    """A cache in front of a slow loader(key). Entries live for ttl seconds
    by clock()."""

    def __init__(self, loader, ttl, clock):
        self.loader = loader
        self.ttl = ttl
        self.clock = clock
        self.entries = {}  # key -> (value, expires at)

    def get(self, key):
        entry = self.entries.get(key)
        if entry and self.clock() < entry[1]:
            return entry[0]
        value = self.loader(key)  # every caller that misses at once loads it again
        self.entries[key] = (value, self.clock() + self.ttl)
        return value


def jittered_ttl(ttl, rng, spread=0.1):
    """ttl scaled by a random factor between 1 - spread and 1 + spread,
    using rng.uniform."""
    raise NotImplementedError


def should_refresh_early(now, expiry, delta, beta, rand):
    """Probabilistic early expiration (XFetch). delta: how long the value
    takes to recompute. rand: uniform in (0, 1]."""
    raise NotImplementedError
