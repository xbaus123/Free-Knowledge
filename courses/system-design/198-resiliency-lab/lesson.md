# Resiliency Patterns: Timeouts, Retries, Circuit Breakers, and Bulkheads

*Chapter 7 · Transactions and Fault Tolerance.*

Build the patterns from the last five readings: deadlines, retries with backoff and a budget, a circuit breaker, and bulkheads.

## Your task

`solution.py` builds these patterns around a `FakeClock`, whose `sleep(seconds)` advances `clock.now` instantly and records the wait in `clock.sleeps`.

### 1. Deadlines

`Deadline(clock, timeout)` ends `timeout` seconds after it's created. `remaining()` and `expired()` are done.

- `timeout_for(default, margin=0.0)` is the timeout for one downstream call: `default`, or the time left minus `margin` if that's smaller. Raise `DeadlineExceeded` if the result isn't positive.
- `to_headers()` returns `{"x-request-deadline-ms": ...}` with the remaining time in whole milliseconds (rounded down), as a string.
- `Deadline.from_headers(clock, headers, default)` builds the deadline a server should use for an incoming request: the caller's remaining time from that header (header names are case-insensitive), but never more than `default`. With no header, or one that isn't an integer, use `default`.

### 2. Retries

- `full_jitter(attempt, base, cap, rng)` returns `rng.uniform(0, min(cap, base × 2^attempt))`, where `attempt` is 0 before the first retry.
- `RetryBudget(ratio, min_retries).can_retry()` is true while `retries < min_retries + ratio × requests`. `record_request` and `record_retry` are done.
- `retry(fn, clock, rng, attempts=4, base=0.1, cap=5.0, deadline=None, budget=None)` calls `fn()` up to `attempts` times and returns its result:
  - Record the request in the budget, if there is one, once per `retry` call.
  - Before each attempt, raise `DeadlineExceeded` if the deadline has passed.
  - Only errors in `RETRYABLE` are retried. Anything else propagates at once.
  - After the last attempt fails, or when the budget can't afford another retry, re-raise the error. Don't sleep first.
  - Otherwise, compute the wait with `full_jitter`. If the deadline would pass during the wait, raise `DeadlineExceeded` instead of sleeping. Then `clock.sleep(wait)`, and record the retry in the budget.

### 3. Circuit breaker

`CircuitBreaker(failure_threshold, reset_timeout).call(fn, now)` calls `fn()` and returns its result, re-raising its exceptions. Keep `self.state` as `"closed"`, `"open"`, or `"half_open"`:

- **Closed**: a failure adds to `self.failures`, and a success resets it to 0. When failures reach the threshold, open the breaker and set `self.opened_at = now`.
- **Open**: if fewer than `reset_timeout` seconds have passed since it opened, raise `CircuitOpen` **without calling** `fn`. Otherwise, go half-open and make this call the trial.
- **Half-open**: a successful trial closes the breaker (failures back to 0); a failed one reopens it at `now`.

### 4. Bulkheads

`Bulkhead(limits, default=10).slot(dependency)` is a context manager (use `@contextmanager`, already imported) that holds one of the dependency's slots for the duration of a `with` block. `limits` maps a dependency to its maximum concurrent calls, and unlisted dependencies get `default`. Count active calls in `self.active[dependency]`. If every slot is taken, raise `BulkheadFull` without taking one. Always give the slot back when the block ends, even if it raised.

Watch a retry loop in the **Scratchpad**:

```python
import random
from solution import Deadline, FakeClock, retry

clock = FakeClock()
attempts = []

def flaky():
    attempts.append(clock.now)
    if len(attempts) < 4:
        raise ConnectionError()
    return "ok"

print(retry(flaky, clock, random.Random(1), deadline=Deadline(clock, 2.0)), clock.sleeps)
```

## Think about it

- The breaker counts consecutive failures. A dependency fails 40% of requests, never twice in a row. What does your breaker do, and what would a failure-rate breaker do instead?
- A request arrives with 30 ms left on its deadline, and your database query usually takes 50 ms. What should the server do, and why is that better than trying?
- Your service calls three dependencies in parallel, and the page can render without two of them. How would you set their timeouts, bulkheads, and fallbacks differently?

## Key terms

| Term | Meaning |
|---|---|
| Fault / failure | One component going wrong / the whole system no longer serving users |
| Cascading failure | A fault spreading from a dependency to everything that waits on it |
| Metastable failure | A system that stays failed after its trigger is gone, held down by its own retries |
| Timeout | How long to wait for one operation before giving up |
| Deadline | An end-to-end time budget, propagated to every hop |
| Exponential backoff | Doubling the wait after each failed attempt, up to a cap |
| Jitter | Randomness in retry waits, so clients don't retry in sync |
| Retry budget | A cap on retries as a fraction of normal requests |
| Hedged request | A duplicate request sent to another replica when the first is slow |
| Circuit breaker | Stops calling a failing dependency for a while, then tests it |
| Bulkhead | A cap on the resources one dependency or tenant can use |
| Shuffle sharding | Giving each customer a random small set of cells, to limit shared blast radius |
| Little's law | Requests in progress = throughput × latency |
| Load shedding | Rejecting excess work quickly to protect a server's capacity |
| Backpressure | A full consumer slowing its producers down |
| Chaos engineering | Injecting faults on purpose to test resilience |
