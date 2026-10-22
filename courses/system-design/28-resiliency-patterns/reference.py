"""Surviving a failing dependency: deadlines, retries with backoff and
jitter, a retry budget, a circuit breaker, and bulkheads."""

from contextlib import contextmanager


class FakeClock:
    """Simulated time: sleep() advances it instantly."""

    def __init__(self, now=0.0):
        self.now = now
        self.sleeps = []

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


# --- 1. Deadlines ------------------------------------------------------------

DEADLINE_HEADER = "x-request-deadline-ms"


class DeadlineExceeded(Exception):
    pass


class Deadline:
    """The moment by which a whole request must finish."""

    def __init__(self, clock, timeout):
        self.clock = clock
        self.at = clock.now + timeout

    def remaining(self):
        return max(0.0, self.at - self.clock.now)

    def expired(self):
        return self.clock.now >= self.at

    def timeout_for(self, default, margin=0.0):
        """The timeout for one downstream call: its usual timeout, cut short
        to leave margin seconds of the deadline for the caller."""
        timeout = min(default, self.at - self.clock.now - margin)
        if timeout <= 0:
            raise DeadlineExceeded()
        return timeout

    def to_headers(self):
        """Propagate the time left, in whole milliseconds, to the next hop."""
        return {DEADLINE_HEADER: str(int(self.remaining() * 1000))}

    @classmethod
    def from_headers(cls, clock, headers, default):
        """The caller's deadline, if it sent one, but never longer than default."""
        raw = {k.lower(): v for k, v in headers.items()}.get(DEADLINE_HEADER)
        try:
            ms = int(raw)
        except (TypeError, ValueError):
            return cls(clock, default)
        return cls(clock, min(max(ms, 0) / 1000, default))


# --- 2. Retries --------------------------------------------------------------


def full_jitter(attempt, base, cap, rng):
    """The wait before retry number attempt (0 for the first retry)."""
    return rng.uniform(0, min(cap, base * 2**attempt))


class RetryBudget:
    """Allows retries of at most ratio × requests, plus min_retries."""

    def __init__(self, ratio=0.1, min_retries=10):
        self.ratio = ratio
        self.min_retries = min_retries
        self.requests = 0
        self.retries = 0

    def record_request(self):
        self.requests += 1

    def can_retry(self):
        """Whether one more retry fits in the budget."""
        return self.retries < self.min_retries + self.ratio * self.requests

    def record_retry(self):
        self.retries += 1


RETRYABLE = (ConnectionError, TimeoutError)


def retry(fn, clock, rng, attempts=4, base=0.1, cap=5.0, deadline=None, budget=None):
    """Call fn(), retrying RETRYABLE errors with full jitter."""
    if budget:
        budget.record_request()
    for attempt in range(attempts):
        if deadline and deadline.expired():
            raise DeadlineExceeded()
        try:
            return fn()
        except RETRYABLE:
            if attempt == attempts - 1 or (budget and not budget.can_retry()):
                raise
            delay = full_jitter(attempt, base, cap, rng)
            if deadline and delay >= deadline.remaining():
                raise DeadlineExceeded() from None
            clock.sleep(delay)
            if budget:
                budget.record_retry()


# --- 3. Circuit breaker ------------------------------------------------------


class CircuitOpen(Exception):
    """The breaker is open: the call was refused without being attempted."""


class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = "closed"
        self.failures = 0
        self.opened_at = None

    def call(self, fn, now):
        """Call fn() through the breaker at time now (seconds)."""
        if self.state == "open":
            if now - self.opened_at < self.reset_timeout:
                raise CircuitOpen()
            self.state = "half_open"
        try:
            result = fn()
        except Exception:
            self.failures += 1
            if self.state == "half_open" or self.failures >= self.failure_threshold:
                self.state = "open"
                self.opened_at = now
            raise
        self.state = "closed"
        self.failures = 0
        return result


# --- 4. Bulkheads ------------------------------------------------------------


class BulkheadFull(Exception):
    """Every slot for this dependency is in use."""


class Bulkhead:
    """Caps concurrent calls per dependency, so one slow dependency can't
    use up every worker. limits: {dependency: max concurrent calls}."""

    def __init__(self, limits, default=10):
        self.limits = dict(limits)
        self.default = default
        self.active = {}

    @contextmanager
    def slot(self, dependency):
        """with bulkhead.slot("payments"): ...  holds one slot during the block."""
        limit = self.limits.get(dependency, self.default)
        if self.active.get(dependency, 0) >= limit:
            raise BulkheadFull(dependency)
        self.active[dependency] = self.active.get(dependency, 0) + 1
        try:
            yield
        finally:
            self.active[dependency] -= 1
