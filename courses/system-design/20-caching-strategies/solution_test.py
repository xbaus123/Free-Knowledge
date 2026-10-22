import random
import threading
import time
import unittest

import solution
from solution import CacheAside, CoalescingCache, LFUCache, SingleFlight, WriteBehind, WriteThrough


class FakeCache:
    def __init__(self):
        self.data = {}
        self.sets = 0

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.sets += 1
        self.data[key] = value

    def delete(self, key):
        self.data.pop(key, None)


class FakeDB:
    def __init__(self):
        self.data = {"user:1": "Ada", "user:2": "Grace"}
        self.reads = 0
        self.writes = 0

    def get(self, key):
        self.reads += 1
        return self.data.get(key)

    def set(self, key, value):
        self.writes += 1
        self.data[key] = value


class LFUTest(unittest.TestCase):
    def test_evicts_least_frequent(self):
        """evicts the least frequently used key"""
        c = LFUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")
        c.get("a")
        c.get("b")
        c.put("c", 3)  # a: 3 uses, b: 2 uses
        self.assertIsNone(c.get("b"))
        self.assertEqual((c.get("a"), c.get("c")), (1, 3))

    def test_ties_go_to_least_recent(self):
        """breaks ties by evicting the least recently used"""
        c = LFUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)  # a and b have one use each; a is older
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.get("b"), 2)

    def test_updates_count_as_use(self):
        """counts an update as a use and keeps the new value"""
        c = LFUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("a", 10)
        c.put("c", 3)
        self.assertEqual(c.get("a"), 10)
        self.assertIsNone(c.get("b"))

    def test_scan_resistance(self):
        """keeps hot keys through a one-off scan, unlike LRU"""
        lru, lfu = solution.LRUCache(3), LFUCache(3)
        for cache in (lru, lfu):
            for key in ("hot-1", "hot-2"):
                cache.put(key, key)
                for _ in range(5):
                    cache.get(key)
            for i in range(10):  # a batch job reads ten cold keys once each
                cache.put(f"cold-{i}", i)
        self.assertIsNone(lru.get("hot-1"), "LRU loses its hot keys to the scan")
        self.assertEqual((lfu.get("hot-1"), lfu.get("hot-2")), ("hot-1", "hot-2"))


class PatternTest(unittest.TestCase):
    def setUp(self):
        self.cache, self.db = FakeCache(), FakeDB()

    def test_cache_aside_reads(self):
        """cache-aside loads misses from the database once"""
        s = CacheAside(self.cache, self.db)
        self.assertEqual([s.read("user:1") for _ in range(3)], ["Ada"] * 3)
        self.assertEqual(self.db.reads, 1)
        self.assertIsNone(s.read("user:9"))
        self.assertNotIn("user:9", self.cache.data, "don't cache a value that doesn't exist (as None)")

    def test_cache_aside_invalidates(self):
        """cache-aside writes the database and deletes the cached copy"""
        s = CacheAside(self.cache, self.db)
        s.read("user:1")
        sets = self.cache.sets
        s.write("user:1", "Ada Lovelace")
        self.assertEqual(self.db.data["user:1"], "Ada Lovelace")
        self.assertNotIn("user:1", self.cache.data, "invalidate rather than update")
        self.assertEqual(self.cache.sets, sets)
        self.assertEqual(s.read("user:1"), "Ada Lovelace")

    def test_write_through(self):
        """write-through updates the database and the cache together"""
        s = WriteThrough(self.cache, self.db)
        s.write("user:3", "Linus")
        self.assertEqual((self.db.data["user:3"], self.cache.data["user:3"]), ("Linus", "Linus"))
        self.assertEqual(s.read("user:3"), "Linus")
        self.assertEqual(self.db.reads, 0, "a write-through value is already cached")

    def test_write_behind(self):
        """write-behind batches writes until flush"""
        s = WriteBehind(self.cache, self.db)
        for i in range(100):
            s.write(f"counter:{i % 3}", i)
        self.assertEqual(self.db.writes, 0, "nothing reaches the database before flush")
        self.assertEqual(s.read("counter:0"), 99)
        s.flush()
        self.assertEqual(self.db.writes, 3, "each key is written once, with its latest value")
        self.assertEqual([self.db.data[f"counter:{i}"] for i in range(3)], [99, 97, 98])
        s.flush()
        self.assertEqual(self.db.writes, 3)

    def test_write_behind_survives_eviction(self):
        """write-behind serves unflushed writes even if the cache drops them"""
        s = WriteBehind(self.cache, self.db)
        s.write("user:1", "Ada Lovelace")
        self.cache.data.clear()  # evicted before the flush
        self.assertEqual(s.read("user:1"), "Ada Lovelace", "the database still has the old value")
        s.flush()
        self.assertEqual(self.db.data["user:1"], "Ada Lovelace")


class StampedeTest(unittest.TestCase):
    def run_together(self, n, fn):
        barrier = threading.Barrier(n)
        results, errors = [None] * n, []

        def worker(i):
            barrier.wait()
            try:
                results[i] = fn()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(5)
        return results, errors

    def test_single_flight(self):
        """runs one call for many concurrent callers of the same key"""
        flight, calls = SingleFlight(), []

        def slow():
            calls.append(1)
            time.sleep(0.2)
            return "report"

        results, errors = self.run_together(20, lambda: flight.do("k", slow))
        self.assertEqual(errors, [])
        self.assertEqual(results, ["report"] * 20)
        self.assertEqual(len(calls), 1, "20 concurrent callers should share one call")
        flight.do("k", slow)
        self.assertEqual(len(calls), 2, "a later call runs again; single flight isn't a cache")

    def test_single_flight_errors(self):
        """shares a failure with every waiting caller"""
        flight = SingleFlight()

        def broken():
            time.sleep(0.1)
            raise ValueError("database down")

        results, errors = self.run_together(5, lambda: flight.do("k", broken))
        self.assertEqual(len(errors), 5)
        self.assertTrue(all(isinstance(e, ValueError) for e in errors))

    def test_keys_are_independent(self):
        """doesn't make different keys wait for each other"""
        flight, calls = SingleFlight(), []

        def load(key):
            calls.append(key)
            time.sleep(0.15)
            return key

        keys = iter(["a", "b"])
        lock = threading.Lock()

        def call():
            with lock:
                key = next(keys)
            return flight.do(key, lambda: load(key))

        start = time.monotonic()
        results, errors = self.run_together(2, call)
        self.assertEqual((errors, sorted(results), sorted(calls)), ([], ["a", "b"], ["a", "b"]))
        self.assertLess(time.monotonic() - start, 0.28, "two different keys should load in parallel")

    def test_coalescing_cache(self):
        """loads an expired key once, however many readers miss at once"""
        now = [0.0]
        loads = []

        def loader(key):
            loads.append(key)
            time.sleep(0.2)
            return f"value of {key}"

        cache = CoalescingCache(loader, ttl=60, clock=lambda: now[0])
        results, errors = self.run_together(20, lambda: cache.get("home"))
        self.assertEqual((errors, results), ([], ["value of home"] * 20))
        self.assertEqual(loads, ["home"])
        now[0] = 59
        cache.get("home")
        self.assertEqual(len(loads), 1)
        now[0] = 60
        self.run_together(20, lambda: cache.get("home"))
        self.assertEqual(len(loads), 2, "after the TTL, one reload")

    def test_jitter(self):
        """spreads TTLs randomly around the base value"""
        rng, mirror = random.Random(4), random.Random(4)
        ttls = [solution.jittered_ttl(300, rng) for _ in range(200)]
        self.assertEqual(ttls, [300 * (1 + mirror.uniform(-0.1, 0.1)) for _ in range(200)])
        self.assertTrue(all(270 <= t <= 330 for t in ttls))
        self.assertGreater(len(set(round(t) for t in ttls)), 30)

    def test_early_refresh(self):
        """refreshes early with rising probability near expiry"""
        f = solution.should_refresh_early
        self.assertTrue(f(now=100, expiry=100, delta=2, beta=1, rand=1.0), "expired")
        self.assertFalse(f(now=90, expiry=100, delta=2, beta=1, rand=0.5))  # 90 + 1.39 < 100
        self.assertTrue(f(now=99, expiry=100, delta=2, beta=1, rand=0.5))  # 99 + 1.39 >= 100
        self.assertTrue(f(now=90, expiry=100, delta=2, beta=1, rand=0.001))  # 90 + 13.8 >= 100
        self.assertFalse(f(now=99, expiry=100, delta=2, beta=0, rand=0.001), "beta 0 disables early refresh")
        self.assertTrue(f(now=95, expiry=100, delta=2, beta=3, rand=0.4))  # 95 + 5.5 >= 100


if __name__ == "__main__":
    unittest.main()
