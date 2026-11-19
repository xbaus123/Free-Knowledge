"""Threads, locks, and the memory hierarchy."""

import threading
import time
from collections import OrderedDict


# --- 1. A race condition ---------------------------------------------------


class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
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
    # Every thread takes the two locks in the same order (lowest id first),
    # so no two threads can each hold one lock while waiting for the other.
    first, second = sorted((source, target), key=lambda account: account.id)
    with first.lock:
        time.sleep(0)
        with second.lock:
            if source.balance < amount:
                raise InsufficientFunds(f"account {source.id} has {source.balance}, needs {amount}")
            source.balance -= amount
            target.balance += amount


# --- 3. The memory hierarchy -------------------------------------------------


class PageCache:
    def __init__(self, capacity, disk):
        self.capacity = capacity
        self.disk = disk
        self.pages = OrderedDict()  # page number -> data, least recently used first
        self.dirty = set()
        self.hits = 0
        self.misses = 0

    def read(self, page):
        if page in self.pages:
            self.hits += 1
            self.pages.move_to_end(page)
            return self.pages[page]
        self.misses += 1
        data = self.disk.read(page)
        self._put(page, data)
        return data

    def write(self, page, data):
        self._put(page, data)
        self.dirty.add(page)

    def flush(self):
        for page in sorted(self.dirty):
            self.disk.write(page, self.pages[page])
        self.dirty.clear()

    def _put(self, page, data):
        self.pages[page] = data
        self.pages.move_to_end(page)
        if len(self.pages) > self.capacity:
            old, old_data = self.pages.popitem(last=False)
            if old in self.dirty:
                self.disk.write(old, old_data)
                self.dirty.discard(old)


def effective_access_ns(hit_rate, cache_ns, backing_ns):
    return hit_rate * cache_ns + (1 - hit_rate) * (cache_ns + backing_ns)
