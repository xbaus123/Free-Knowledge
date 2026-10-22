import unittest

from solution import (
    CircuitBreaker,
    CircuitOpen,
    Crash,
    IdempotencyStore,
    Saga,
    Step,
    availability,
    find_cycle,
)

# --- Dependency analysis -----------------------------------------------------

SHOP = {
    "web": ["cart", "catalog", "auth"],
    "cart": ["pricing", "inventory", "auth"],
    "catalog": ["search", "pricing"],
    "pricing": ["discounts"],
    "inventory": [],
    "auth": [],
    "search": [],
    "discounts": [],
}


def is_cycle(graph, cycle):
    return (
        len(cycle) >= 2
        and cycle[0] == cycle[-1]
        and len(set(cycle[:-1])) == len(cycle) - 1
        and all(b in graph.get(a, []) for a, b in zip(cycle, cycle[1:]))
    )


class DependencyTest(unittest.TestCase):
    def test_no_cycle(self):
        """returns None for an acyclic call graph"""
        self.assertIsNone(find_cycle(SHOP))
        self.assertIsNone(find_cycle({}))

    def test_cycle(self):
        """finds a cycle of synchronous calls"""
        graph = {**SHOP, "discounts": ["cart"]}  # discounts now calls back into cart
        cycle = find_cycle(graph)
        self.assertIsNotNone(cycle)
        self.assertTrue(is_cycle(graph, cycle), cycle)
        self.assertEqual(set(cycle), {"cart", "pricing", "discounts"})

    def test_self_loop_and_diamonds(self):
        """handles self-calls, and shared dependencies that aren't cycles"""
        self.assertEqual(find_cycle({"a": ["a"]}), ["a", "a"])
        diamond = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": []}
        self.assertIsNone(find_cycle(diamond))
        cycle = find_cycle({"x": ["y"], "y": ["z"], "z": ["w"], "w": ["y"]})
        self.assertEqual(set(cycle), {"y", "z", "w"})

    def test_availability(self):
        """multiplies the availability of everything a service needs"""
        slo = {s: 0.999 for s in SHOP}
        self.assertAlmostEqual(availability(SHOP, slo, "inventory"), 0.999)
        self.assertAlmostEqual(availability(SHOP, slo, "pricing"), 0.999**2)
        self.assertAlmostEqual(availability(SHOP, slo, "web"), 0.999**8, msg="auth and pricing count once")

    def test_availability_cycle(self):
        """terminates on a cyclic graph"""
        graph = {"a": ["b"], "b": ["c"], "c": ["a"]}
        self.assertAlmostEqual(availability(graph, {"a": 0.99, "b": 0.9, "c": 0.5}, "a"), 0.99 * 0.9 * 0.5)


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


# --- Sagas -------------------------------------------------------------------


class Service:
    """A fake participant that applies each key's effect once."""

    def __init__(self, name, record, fail=0, crash_after=False):
        self.name = name
        self.record = record
        self.fail = fail  # how many calls to fail before succeeding
        self.crash_after = crash_after  # crash the orchestrator after applying
        self.applied = set()

    def __call__(self, ctx, key):
        if self.fail:
            self.fail -= 1
            raise RuntimeError(f"{self.name} failed")
        if key not in self.applied:
            self.applied.add(key)
            self.record.append((self.name, key))
        if self.crash_after:
            self.crash_after = False
            raise Crash()


def order_saga(record, **overrides):
    names = [
        ("reserve", "release"),
        ("charge", "refund"),
        ("ship", "cancel_shipment"),
    ]
    steps = []
    for action, comp in names:
        a = overrides.get(action) or Service(action, record)
        c = overrides.get(comp) or Service(comp, record)
        steps.append(Step(action, a, c))
    return steps


def names(record):
    return [name for name, _ in record]


class SagaTest(unittest.TestCase):
    def test_completes(self):
        """runs every step in order"""
        record, log = [], []
        self.assertEqual(Saga(order_saga(record), log).run("o1", {}), "completed")
        self.assertEqual(record, [("reserve", "o1/reserve"), ("charge", "o1/charge"), ("ship", "o1/ship")])
        self.assertEqual(log, [("o1", "reserve", "done"), ("o1", "charge", "done"), ("o1", "ship", "done"), ("o1", None, "completed")])

    def test_compensates(self):
        """undoes completed steps in reverse order when a step fails"""
        record, log = [], []
        steps = order_saga(record, ship=Service("ship", record, fail=1))
        self.assertEqual(Saga(steps, log).run("o2", {}), "compensated")
        self.assertEqual(names(record), ["reserve", "charge", "refund", "release"])
        self.assertEqual(record[2], ("refund", "o2/charge"), "a compensation gets its step's key")
        self.assertEqual(
            log,
            [
                ("o2", "reserve", "done"),
                ("o2", "charge", "done"),
                ("o2", "ship", "failed"),
                ("o2", "charge", "compensated"),
                ("o2", "reserve", "compensated"),
                ("o2", None, "compensated"),
            ],
        )

    def test_first_step_fails(self):
        """has nothing to undo when the first step fails"""
        record, log = [], []
        steps = order_saga(record, reserve=Service("reserve", record, fail=1))
        self.assertEqual(Saga(steps, log).run("o3", {}), "compensated")
        self.assertEqual(record, [])

    def test_retries_compensations(self):
        """retries a failing compensation"""
        record, log = [], []
        steps = order_saga(record, ship=Service("ship", record, fail=1), refund=Service("refund", record, fail=2))
        self.assertEqual(Saga(steps, log, max_retries=3).run("o4", {}), "compensated")
        self.assertEqual(names(record), ["reserve", "charge", "refund", "release"])

    def test_stuck(self):
        """stops and reports stuck when a compensation keeps failing"""
        record, log = [], []
        steps = order_saga(record, ship=Service("ship", record, fail=1), refund=Service("refund", record, fail=99))
        self.assertEqual(Saga(steps, log, max_retries=3).run("o5", {}), "stuck")
        self.assertEqual(names(record), ["reserve", "charge"], "doesn't skip ahead to release")
        self.assertEqual(log[-1], ("o5", None, "stuck"))

    def test_resume_after_crash(self):
        """resumes from the log after a crash, without redoing finished steps"""
        record, log = [], []
        charge = Service("charge", record, crash_after=True)
        steps = order_saga(record, charge=charge)
        with self.assertRaises(Crash):
            Saga(steps, log).run("o6", {})
        self.assertEqual(log, [("o6", "reserve", "done")], "the crash came before charge was logged")
        # A new orchestrator process, with the same durable log.
        self.assertEqual(Saga(steps, log).run("o6", {}), "completed")
        self.assertEqual(names(record), ["reserve", "charge", "ship"], "charge ran again with the same key")
        self.assertEqual(log.count(("o6", "reserve", "done")), 1)

    def test_resume_compensation(self):
        """resumes a crashed compensation where it left off"""
        record, log = [], []
        refund = Service("refund", record, crash_after=True)
        release = Service("release", record)
        steps = order_saga(record, ship=Service("ship", record, fail=1), refund=refund, release=release)
        with self.assertRaises(Crash):
            Saga(steps, log).run("o7", {})
        self.assertEqual(Saga(steps, log).run("o7", {}), "compensated")
        self.assertEqual(names(record), ["reserve", "charge", "refund", "release"])
        self.assertEqual(log[-3:], [("o7", "charge", "compensated"), ("o7", "reserve", "compensated"), ("o7", None, "compensated")])

    def test_finished(self):
        """returns a finished saga's outcome without running anything"""
        record, log = [], []
        steps = order_saga(record)
        Saga(steps, log).run("o8", {})
        before = list(log)
        self.assertEqual(Saga(steps, log).run("o8", {}), "completed")
        self.assertEqual(log, before)
        self.assertEqual(len(record), 3)

    def test_independent_sagas(self):
        """keeps sagas sharing one log separate"""
        record, log = [], []
        steps = order_saga(record)
        Saga(steps, log).run("a", {})
        self.assertEqual(Saga(steps, log).run("b", {}), "completed")
        self.assertEqual(len(record), 6)

    def test_context(self):
        """passes the same context to every step"""
        seen = []
        steps = [Step(n, lambda ctx, key, n=n: seen.append((n, ctx["order"])), lambda ctx, key: None) for n in "xyz"]
        Saga(steps, []).run("c", {"order": 42})
        self.assertEqual(seen, [("x", 42), ("y", 42), ("z", 42)])


class IdempotencyTest(unittest.TestCase):
    def test_once(self):
        """runs an operation once per key and replays its result"""
        store, calls = IdempotencyStore(), []

        def charge():
            calls.append(1)
            return {"charge_id": len(calls)}

        self.assertEqual(store.run("order-1", charge), {"charge_id": 1})
        self.assertEqual(store.run("order-1", charge), {"charge_id": 1})
        self.assertEqual(store.run("order-2", charge), {"charge_id": 2})
        self.assertEqual(len(calls), 2)

    def test_failures_not_remembered(self):
        """lets a failed operation be retried"""
        store, attempts = IdempotencyStore(), []

        def flaky():
            attempts.append(1)
            if len(attempts) == 1:
                raise TimeoutError()
            return "done"

        with self.assertRaises(TimeoutError):
            store.run("k", flaky)
        self.assertEqual(store.run("k", flaky), "done")
        self.assertEqual(store.run("k", flaky), "done")
        self.assertEqual(len(attempts), 2)


if __name__ == "__main__":
    unittest.main()
