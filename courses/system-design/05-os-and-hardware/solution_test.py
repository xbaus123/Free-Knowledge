import random
import sys
import threading
import time
import unittest

import solution
from solution import Account, Counter, InsufficientFunds, PageCache, transfer


def run_threads(targets, timeout=3):
    """Runs each function in its own thread. Returns the threads still
    running after the timeout (stuck in a deadlock)."""
    errors = []

    def wrap(fn):
        def run():
            try:
                fn()
            except Exception as e:  # surfaced by the test
                errors.append(e)

        return run

    threads = [threading.Thread(target=wrap(fn), daemon=True) for fn in targets]
    for t in threads:
        t.start()
    deadline = time.monotonic() + timeout
    for t in threads:
        t.join(max(0, deadline - time.monotonic()))
    stuck = [t for t in threads if t.is_alive()]
    return stuck, errors


class ThreadTest(unittest.TestCase):
    def setUp(self):
        self.interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)  # switch threads as often as possible

    def tearDown(self):
        sys.setswitchinterval(self.interval)


class CounterTest(ThreadTest):
    def test_counts_one_thread(self):
        """counts correctly with one thread"""
        c = Counter()
        for _ in range(100):
            c.increment()
        self.assertEqual(c.value, 100)

    def test_no_lost_updates(self):
        """loses no increments when 8 threads share the counter"""
        c = Counter()
        stuck, errors = run_threads([lambda: [c.increment() for _ in range(500)]] * 8)
        self.assertEqual((stuck, errors), ([], []))
        self.assertEqual(c.value, 4000, "two threads read the same value and both wrote value + 1")


class TransferTest(ThreadTest):
    def test_moves_money(self):
        """moves money between accounts"""
        a, b = Account(1, 100), Account(2, 50)
        transfer(a, b, 30)
        self.assertEqual((a.balance, b.balance), (70, 80))

    def test_insufficient_funds(self):
        """refuses to overdraw, changes nothing, and releases its locks"""
        a, b = Account(1, 10), Account(2, 0)
        with self.assertRaises(InsufficientFunds):
            transfer(a, b, 11)
        self.assertEqual((a.balance, b.balance), (10, 0))
        for account in (a, b):
            self.assertTrue(account.lock.acquire(blocking=False), "a lock was left held")
            account.lock.release()

    def test_opposite_directions(self):
        """doesn't deadlock when two threads transfer in opposite directions"""
        a, b = Account(1, 1000), Account(2, 1000)

        def forward():
            for _ in range(300):
                transfer(a, b, 1)

        def backward():
            for _ in range(300):
                transfer(b, a, 1)

        stuck, errors = run_threads([forward, backward] * 4)
        self.assertEqual(stuck, [], "threads are stuck: each holds one lock and waits for the other")
        self.assertEqual(errors, [])
        self.assertEqual((a.balance, b.balance), (1000, 1000))

    def test_many_accounts(self):
        """conserves money with random transfers among many accounts"""
        accounts = [Account(i, 100) for i in range(5, 0, -1)]

        def worker(seed):
            rng = random.Random(seed)

            def run():
                for _ in range(300):
                    source, target = rng.sample(accounts, 2)
                    try:
                        transfer(source, target, rng.randint(1, 30))
                    except InsufficientFunds:
                        pass

            return run

        stuck, errors = run_threads([worker(seed) for seed in range(8)])
        self.assertEqual(stuck, [], "deadlock")
        self.assertEqual(errors, [])
        self.assertEqual(sum(a.balance for a in accounts), 500, "money was created or destroyed")
        self.assertTrue(all(a.balance >= 0 for a in accounts), "an account was overdrawn")


class FakeDisk:
    def __init__(self):
        self.data = {page: f"page {page}" for page in range(100)}
        self.reads = 0
        self.writes = 0

    def read(self, page):
        self.reads += 1
        return self.data[page]

    def write(self, page, data):
        self.writes += 1
        self.data[page] = data


class PageCacheTest(unittest.TestCase):
    def setUp(self):
        self.disk = FakeDisk()

    def test_hits_and_misses(self):
        """serves repeated reads from memory"""
        cache = PageCache(2, self.disk)
        self.assertEqual(cache.read(1), "page 1")
        self.assertEqual(cache.read(2), "page 2")
        self.assertEqual(cache.read(1), "page 1")
        self.assertEqual((cache.hits, cache.misses, self.disk.reads), (1, 2, 2))

    def test_evicts_least_recently_used(self):
        """evicts the least recently used page when full"""
        cache = PageCache(2, self.disk)
        cache.read(1)
        cache.read(2)
        cache.read(1)  # now 2 is the least recently used
        cache.read(3)  # evicts 2
        reads = self.disk.reads
        cache.read(1)
        cache.read(3)
        self.assertEqual(self.disk.reads, reads, "pages 1 and 3 should still be cached")
        cache.read(2)
        self.assertEqual(self.disk.reads, reads + 1, "page 2 should have been evicted")

    def test_write_back(self):
        """keeps writes in memory until flush"""
        cache = PageCache(4, self.disk)
        cache.write(5, "new")
        self.assertEqual(self.disk.writes, 0, "a write stays in memory until it's flushed or evicted")
        self.assertEqual(cache.read(5), "new")
        self.assertEqual(self.disk.reads, 0, "a page you just wrote is cached")
        cache.write(5, "newer")
        cache.write(6, "six")
        cache.flush()
        self.assertEqual(self.disk.writes, 2, "flush writes each changed page once")
        self.assertEqual((self.disk.data[5], self.disk.data[6]), ("newer", "six"))
        cache.flush()
        self.assertEqual(self.disk.writes, 2, "flushed pages are clean until they change again")

    def test_eviction_writes_dirty_pages(self):
        """writes a changed page to disk when it's evicted, and only then"""
        cache = PageCache(1, self.disk)
        cache.read(1)
        cache.read(2)
        self.assertEqual(self.disk.writes, 0, "evicting an unchanged page needs no write")
        cache.write(2, "changed")
        cache.read(3)
        self.assertEqual(self.disk.writes, 1)
        self.assertEqual(self.disk.data[2], "changed", "evicting a changed page must not lose it")
        self.assertEqual(cache.read(2), "changed")
        cache.flush()
        self.assertEqual(self.disk.writes, 1)

    def test_working_set(self):
        """gets a high hit rate when the working set fits in memory"""
        cache = PageCache(10, self.disk)
        rng = random.Random(1)
        for _ in range(1000):
            page = rng.randrange(8) if rng.random() < 0.9 else rng.randrange(8, 100)
            cache.read(page)
        self.assertEqual(cache.hits + cache.misses, 1000)
        self.assertGreater(cache.hits / 1000, 0.8)


class AccessTimeTest(unittest.TestCase):
    def test_effective_access_time(self):
        """a few misses dominate the average access time"""
        self.assertAlmostEqual(solution.effective_access_ns(1.0, 100, 100_000), 100)
        self.assertAlmostEqual(solution.effective_access_ns(0.0, 100, 100_000), 100_100)
        self.assertAlmostEqual(solution.effective_access_ns(0.99, 100, 100_000), 1_100)
        self.assertAlmostEqual(solution.effective_access_ns(0.9, 100, 10_000_000), 1_000_100)


if __name__ == "__main__":
    unittest.main()
