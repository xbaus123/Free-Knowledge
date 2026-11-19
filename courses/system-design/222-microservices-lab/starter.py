"""Microservice building blocks: dependency analysis, idempotent handlers,
and a saga orchestrator that survives crashes."""


# --- 1. Dependency analysis --------------------------------------------------


def find_cycle(graph):
    """graph: {service: [services it calls synchronously]}. Return one cycle
    as a list that starts and ends with the same service, or None."""
    raise NotImplementedError


def availability(graph, slo, service):
    """The fraction of time service and everything it calls synchronously
    are all up, if each fails independently. slo: {service: availability}."""
    raise NotImplementedError


# --- 2. Sagas ----------------------------------------------------------------


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
