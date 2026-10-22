"""Threads, locks, and the memory hierarchy.

Three parts: fix a race condition, fix a deadlock, and put a page cache
in front of a slow disk. The lesson explains each one.
"""

import threading
import time


# --- 1. A race condition ---------------------------------------------------


class Counter:
    """Many threads call increment() at once. Some increments get lost."""

    def __init__(self):
        self.value = 0

    def increment(self):
        current = self.value
        time.sleep(0)  # the scheduler may switch threads here
        self.value = current + 1


# --- 2. Deadlock -----------------------------------------------------------


class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, id, balance):
        self.id = id
        self.balance = balance
        self.lock = threading.Lock()


def transfer(source, target, amount):
    """Move amount from source to target while other threads transfer too.

    Raise InsufficientFunds, changing nothing, if source has less than
    amount. Run two of these at once in opposite directions and they can
    wait for each other forever.
    """
    with source.lock:
        time.sleep(0)
        with target.lock:
            source.balance -= amount
            target.balance += amount


# --- 3. The memory hierarchy -------------------------------------------------


class PageCache:
    """Keeps up to capacity pages in memory in front of a slow disk.

    disk.read(page) and disk.write(page, data) are slow: avoid them.
    """

    def __init__(self, capacity, disk):
        self.capacity = capacity
        self.disk = disk
        self.hits = 0
        self.misses = 0

    def read(self, page):
        """Return the page's data, from memory if it's cached. When the
        cache is full, evict the least recently used page."""
        return self.disk.read(page)

    def write(self, page, data):
        """Update the page in memory only. It reaches the disk when it's
        evicted or flushed."""
        self.disk.write(page, data)

    def flush(self):
        """Write every page that changed since it was last written to disk."""


def effective_access_ns(hit_rate, cache_ns, backing_ns):
    """The average time per access. A hit costs cache_ns; a miss checks the
    cache first and then goes to the backing store."""
    raise NotImplementedError
