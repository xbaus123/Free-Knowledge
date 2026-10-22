"""Microservice building blocks: dependency analysis, a circuit breaker,
idempotent handlers, and a saga orchestrator that survives crashes."""


# --- 1. Dependency analysis --------------------------------------------------


def find_cycle(graph):
    """graph: {service: [services it calls synchronously]}. Return one cycle
    as a list that starts and ends with the same service, or None."""
    raise NotImplementedError


def availability(graph, slo, service):
    """The fraction of time service and everything it calls synchronously
    are all up, if each fails independently. slo: {service: availability}."""
    raise NotImplementedError


# --- 2. Circuit breaker ------------------------------------------------------


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
        raise NotImplementedError


# --- 3. Sagas ----------------------------------------------------------------


class Crash(BaseException):
    """The orchestrator process died. Not an Exception, so `except Exception`
    doesn't catch it: it unwinds everything, like a real crash."""


class IdempotencyStore:
    """Remembers the result of each operation by its idempotency key."""

    def __init__(self):
        self.results = {}

    def run(self, key, fn):
        """Run fn() the first time key is seen and return its result. Later
        calls with the same key return that result without running fn."""
        raise NotImplementedError


class Step:
    def __init__(self, name, action, compensation):
        self.name = name
        self.action = action  # action(ctx, key)
        self.compensation = compensation  # compensation(ctx, key)


class Saga:
    """Runs steps in order. log is a durable list of (saga_id, step name or
    None, event) tuples, shared by every orchestrator process."""

    def __init__(self, steps, log, max_retries=3):
        self.steps = steps
        self.log = log
        self.max_retries = max_retries

    def run(self, saga_id, ctx):
        """Run (or resume) saga saga_id: "completed", "compensated", or "stuck"."""
        raise NotImplementedError
