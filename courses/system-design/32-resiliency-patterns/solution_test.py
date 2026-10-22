import random
import unittest

from solution import (
    Bulkhead,
    BulkheadFull,
    CircuitBreaker,
    CircuitOpen,
    Deadline,
    DeadlineExceeded,
    FakeClock,
    RetryBudget,
    full_jitter,
    retry,
)


class MaxRng:
    """A fake random source: uniform(a, b) always returns b."""

    def __init__(self):
        self.calls = []

    def uniform(self, a, b):
        self.calls.append((a, b))
        return b


class Flaky:
    """Fails with the given exceptions, in order, then succeeds."""

    def __init__(self, *errors):
        self.errors = list(errors)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return "ok"


# --- Deadlines ---------------------------------------------------------------


class DeadlineTest(unittest.TestCase):
    def test_remaining(self):
        """counts down to the deadline"""
        clock = FakeClock(100)
        d = Deadline(clock, 2.0)
        clock.now = 101.5
        self.assertAlmostEqual(d.remaining(), 0.5)
        self.assertFalse(d.expired())
        clock.now = 103
        self.assertEqual(d.remaining(), 0.0)
        self.assertTrue(d.expired())

    def test_timeout_for(self):
        """shortens a call's timeout to fit what's left"""
        clock = FakeClock()
        d = Deadline(clock, 1.0)
        self.assertAlmostEqual(d.timeout_for(0.3), 0.3, msg="plenty of time: the usual timeout")
        clock.now = 0.8
        self.assertAlmostEqual(d.timeout_for(0.3), 0.2)
        self.assertAlmostEqual(d.timeout_for(0.3, margin=0.05), 0.15, msg="leave the caller time to respond")
        with self.assertRaises(DeadlineExceeded):
            d.timeout_for(0.3, margin=0.2)
        clock.now = 1.0
        with self.assertRaises(DeadlineExceeded):
            d.timeout_for(0.3)

    def test_propagation(self):
        """passes the time left to the next hop as a relative duration"""
        clock = FakeClock(1_700_000_000)
        d = Deadline(clock, 0.75)
        clock.now += 0.2501
        self.assertEqual(d.to_headers(), {"x-request-deadline-ms": "499"})
        downstream_clock = FakeClock(42)  # another machine, another clock
        child = Deadline.from_headers(downstream_clock, d.to_headers(), default=5.0)
        self.assertAlmostEqual(child.remaining(), 0.499)

    def test_from_headers(self):
        """caps the caller's deadline and falls back on the default"""
        clock = FakeClock()
        self.assertAlmostEqual(Deadline.from_headers(clock, {"X-Request-Deadline-Ms": "250"}, 1.0).remaining(), 0.25)
        self.assertAlmostEqual(Deadline.from_headers(clock, {"x-request-deadline-ms": "60000"}, 1.0).remaining(), 1.0)
        self.assertAlmostEqual(Deadline.from_headers(clock, {}, 1.0).remaining(), 1.0)
        self.assertAlmostEqual(Deadline.from_headers(clock, {"x-request-deadline-ms": "soon"}, 1.0).remaining(), 1.0)
        self.assertTrue(Deadline.from_headers(clock, {"x-request-deadline-ms": "0"}, 1.0).expired())


# --- Retries -----------------------------------------------------------------


class BackoffTest(unittest.TestCase):
    def test_exponential(self):
        """doubles the maximum wait each attempt, up to the cap"""
        rng = MaxRng()
        self.assertEqual([full_jitter(a, 0.1, 5.0, rng) for a in range(8)], [0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 5.0, 5.0])
        self.assertEqual(rng.calls[0], (0, 0.1), "full jitter draws from 0 up to the backoff")

    def test_jitter_spreads_retries(self):
        """spreads clients' retries across the whole window"""
        rng = random.Random(9)
        waits = [full_jitter(3, 0.1, 5.0, rng) for _ in range(2000)]
        self.assertTrue(all(0 <= w <= 0.8 for w in waits))
        buckets = [0] * 8
        for w in waits:
            buckets[min(int(w / 0.1), 7)] += 1
        self.assertTrue(all(180 < b < 320 for b in buckets), buckets)


class RetryTest(unittest.TestCase):
    def test_success(self):
        """returns at once when the first call works"""
        clock = FakeClock()
        self.assertEqual(retry(Flaky(), clock, MaxRng()), "ok")
        self.assertEqual(clock.sleeps, [])

    def test_retries_transient(self):
        """retries connection errors and timeouts, backing off"""
        clock, fn = FakeClock(), Flaky(ConnectionError(), TimeoutError(), ConnectionError())
        self.assertEqual(retry(fn, clock, MaxRng(), attempts=4, base=0.1), "ok")
        self.assertEqual(fn.calls, 4)
        self.assertEqual(clock.sleeps, [0.1, 0.2, 0.4])

    def test_gives_up(self):
        """raises the last error after the final attempt, without a pointless wait"""
        clock, fn = FakeClock(), Flaky(*[ConnectionError(str(i)) for i in range(10)])
        with self.assertRaises(ConnectionError) as ctx:
            retry(fn, clock, MaxRng(), attempts=3)
        self.assertEqual(str(ctx.exception), "2")
        self.assertEqual(fn.calls, 3)
        self.assertEqual(len(clock.sleeps), 2)

    def test_permanent_errors(self):
        """doesn't retry errors that will never succeed"""
        clock, fn = FakeClock(), Flaky(ValueError("bad request"))
        with self.assertRaises(ValueError):
            retry(fn, clock, MaxRng())
        self.assertEqual(fn.calls, 1)
        self.assertEqual(clock.sleeps, [])

    def test_deadline_stops_waiting(self):
        """gives up instead of sleeping past the deadline"""
        clock = FakeClock()
        fn = Flaky(*[TimeoutError() for _ in range(10)])
        deadline = Deadline(clock, 0.5)
        with self.assertRaises(DeadlineExceeded):
            retry(fn, clock, MaxRng(), attempts=10, base=0.1, deadline=deadline)
        self.assertEqual(clock.sleeps, [0.1, 0.2], "the next wait, 0.4, would pass the deadline")
        self.assertEqual(fn.calls, 3)

    def test_expired_deadline(self):
        """doesn't call at all once the deadline has passed"""
        clock = FakeClock()
        deadline = Deadline(clock, 0.1)
        clock.now = 1
        fn = Flaky()
        with self.assertRaises(DeadlineExceeded):
            retry(fn, clock, MaxRng(), deadline=deadline)
        self.assertEqual(fn.calls, 0)

    def test_budget(self):
        """stops retrying when the retry budget is spent"""
        budget = RetryBudget(ratio=0.1, min_retries=2)
        clock = FakeClock()
        always_down = Flaky(*[ConnectionError() for _ in range(1000)])
        failures = 0
        for _ in range(20):
            try:
                retry(always_down, clock, MaxRng(), attempts=3, budget=budget)
            except ConnectionError:
                failures += 1
        self.assertEqual(failures, 20)
        self.assertEqual(budget.requests, 20)
        self.assertEqual(budget.retries, 4, "2 free retries, plus 10% of 20 requests")
        self.assertEqual(always_down.calls, 24, "versus 60 if every request retried twice")

    def test_budget_math(self):
        """allows retries up to the ratio of requests"""
        b = RetryBudget(ratio=0.2, min_retries=0)
        self.assertFalse(b.can_retry())
        for _ in range(10):
            b.record_request()
        self.assertTrue(b.can_retry())
        b.record_retry()
        self.assertTrue(b.can_retry())
        b.record_retry()
        self.assertFalse(b.can_retry())


# --- Circuit breaker ---------------------------------------------------------


def ok():
    return "ok"


def boom():
    raise ConnectionError("upstream down")


class CircuitBreakerTest(unittest.TestCase):
    def test_closed(self):
        """passes calls and errors through while closed"""
        cb = CircuitBreaker(failure_threshold=3)
        self.assertEqual(cb.call(ok, 0), "ok")
        with self.assertRaises(ConnectionError):
            cb.call(boom, 1)
        self.assertEqual(cb.state, "closed")

    def test_opens(self):
        """opens after consecutive failures, and fails fast"""
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=30)
        for t in range(3):
            with self.assertRaises(ConnectionError):
                cb.call(boom, t)
        self.assertEqual(cb.state, "open")
        calls = []
        with self.assertRaises(CircuitOpen):
            cb.call(lambda: calls.append(1), 10)
        self.assertEqual(calls, [], "an open breaker doesn't call the service")

    def test_success_resets(self):
        """counts only consecutive failures"""
        cb = CircuitBreaker(failure_threshold=3)
        for t, fn in enumerate([boom, boom, ok, boom, boom]):
            try:
                cb.call(fn, t)
            except ConnectionError:
                pass
        self.assertEqual(cb.state, "closed")

    def test_half_open_success(self):
        """closes again when the trial call succeeds"""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=30)
        with self.assertRaises(ConnectionError):
            cb.call(boom, 100)
        with self.assertRaises(CircuitOpen):
            cb.call(ok, 129)
        self.assertEqual(cb.call(ok, 130), "ok")
        self.assertEqual(cb.state, "closed")
        self.assertEqual(cb.failures, 0)

    def test_half_open_failure(self):
        """reopens at once when the trial call fails"""
        cb = CircuitBreaker(failure_threshold=5, reset_timeout=30)
        for t in range(5):
            with self.assertRaises(ConnectionError):
                cb.call(boom, t)
        with self.assertRaises(ConnectionError):
            cb.call(boom, 40)  # the trial
        self.assertEqual(cb.state, "open")
        with self.assertRaises(CircuitOpen):
            cb.call(ok, 69)
        self.assertEqual(cb.call(ok, 70), "ok")

    def test_with_retries(self):
        """stops a retry loop as soon as the breaker opens"""
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=30)
        clock, fn = FakeClock(), Flaky(*[ConnectionError() for _ in range(10)])
        with self.assertRaises(CircuitOpen):
            retry(lambda: cb.call(fn, clock.now), clock, MaxRng(), attempts=5)
        self.assertEqual(fn.calls, 2, "CircuitOpen isn't retryable: the dependency is known to be down")


# --- Bulkheads ---------------------------------------------------------------


class BulkheadTest(unittest.TestCase):
    def test_limits(self):
        """caps concurrent calls per dependency"""
        b = Bulkhead({"payments": 2})
        with b.slot("payments"):
            with b.slot("payments"):
                self.assertEqual(b.active["payments"], 2)
                with self.assertRaises(BulkheadFull):
                    with b.slot("payments"):
                        pass
        self.assertEqual(b.active["payments"], 0)

    def test_isolation(self):
        """keeps a saturated dependency from blocking others"""
        b = Bulkhead({"recommendations": 1, "payments": 1})
        with b.slot("recommendations"):
            with self.assertRaises(BulkheadFull):
                with b.slot("recommendations"):
                    pass
            with b.slot("payments"):
                pass

    def test_releases_on_error(self):
        """frees the slot when the call raises"""
        b = Bulkhead({"search": 1})
        with self.assertRaises(TimeoutError):
            with b.slot("search"):
                raise TimeoutError()
        with b.slot("search"):
            pass
        self.assertEqual(b.active["search"], 0)

    def test_full_doesnt_leak(self):
        """doesn't count a rejected call as active"""
        b = Bulkhead({"x": 1})
        with b.slot("x"):
            for _ in range(5):
                with self.assertRaises(BulkheadFull):
                    with b.slot("x"):
                        pass
            self.assertEqual(b.active["x"], 1)

    def test_default(self):
        """uses the default limit for unlisted dependencies"""
        b = Bulkhead({}, default=3)
        with b.slot("a"), b.slot("a"), b.slot("a"):
            with self.assertRaises(BulkheadFull):
                with b.slot("a"):
                    pass


if __name__ == "__main__":
    unittest.main()
