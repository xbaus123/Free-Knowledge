"""Microservice building blocks: dependency analysis, a circuit breaker,
idempotent handlers, and a saga orchestrator that survives crashes."""


# --- 1. Dependency analysis --------------------------------------------------


def find_cycle(graph):
    """graph: {service: [services it calls synchronously]}. Return one cycle
    as a list that starts and ends with the same service, or None."""
    state = {}  # service -> "visiting" or "done"
    path = []

    def visit(service):
        state[service] = "visiting"
        path.append(service)
        for dep in graph.get(service, []):
            if state.get(dep) == "visiting":
                return path[path.index(dep) :] + [dep]
            if dep not in state:
                cycle = visit(dep)
                if cycle:
                    return cycle
        path.pop()
        state[service] = "done"
        return None

    for service in graph:
        if service not in state:
            cycle = visit(service)
            if cycle:
                return cycle
    return None


def dependencies(graph, service):
    """Every service that service needs, directly or indirectly."""
    seen, todo = set(), list(graph.get(service, []))
    while todo:
        dep = todo.pop()
        if dep != service and dep not in seen:
            seen.add(dep)
            todo.extend(graph.get(dep, []))
    return seen


def availability(graph, slo, service):
    """The fraction of time service and everything it calls synchronously
    are all up, if each fails independently. slo: {service: availability}."""
    result = slo[service]
    for dep in dependencies(graph, service):
        result *= slo[dep]
    return result


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
        if key not in self.results:
            self.results[key] = fn()
        return self.results[key]


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
        events = {(step, event) for sid, step, event in self.log if sid == saga_id}
        for status in ("completed", "compensated", "stuck"):
            if (None, status) in events:
                return status
        done = [s for s in self.steps if (s.name, "done") in events]
        if not any(event == "failed" for _, event in events):
            for step in self.steps:
                if step in done:
                    continue
                try:
                    step.action(ctx, f"{saga_id}/{step.name}")
                except Exception:
                    self.log.append((saga_id, step.name, "failed"))
                    break
                self.log.append((saga_id, step.name, "done"))
                done.append(step)
            else:
                self.log.append((saga_id, None, "completed"))
                return "completed"
        return self._compensate(saga_id, ctx, done, events)

    def _compensate(self, saga_id, ctx, done, events):
        for step in reversed(done):
            if (step.name, "compensated") in events:
                continue
            for _ in range(self.max_retries):
                try:
                    step.compensation(ctx, f"{saga_id}/{step.name}")
                    break
                except Exception:
                    pass
            else:
                self.log.append((saga_id, None, "stuck"))
                return "stuck"
            self.log.append((saga_id, step.name, "compensated"))
        self.log.append((saga_id, None, "compensated"))
        return "compensated"
