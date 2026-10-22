# Resiliency Patterns: Timeouts, Retries, Circuit Breakers, and Bulkheads

*Based on* Designing Data-Intensive Applications*, Chapters 1 and 8.*

The last lesson was the diagnosis. Networks lose and delay messages without bound, processes pause, clocks drift, and a timeout can't tell a dead node from a slow one. This lesson is the treatment: the patterns that keep a system working while the things it depends on are failing.

Lesson 1 drew the line between a **fault** (one component deviating from its spec) and a **failure** (the system as a whole stops serving users). You can't prevent faults. These patterns stop them from turning into failures, and above all from **spreading**.

## How small faults become outages

Most large outages don't start large. They start with one slow dependency, and the system's own reactions make it worse.

**Cascading failure.** A recommendations service slows from 20 ms to 2 seconds, perhaps because of a garbage collection storm. The product page calls it synchronously with no timeout. The page servers have 200 worker threads each. Each request now holds a thread for 2 seconds instead of 50 ms, so the servers handle 100 requests a second instead of 4,000. Their queues fill, their own latency soars, and the gateway's calls to them time out. A slow, *non-essential* feature has taken down the product page, and anything else that shared those threads.

**Retry storms.** Clients that time out retry. Each retry is another request to an already overloaded service. If each of four layers retries 3 times, one failing call at the bottom becomes 3⁴ = 81 attempts, and the struggling service sees its load multiply exactly when it can least afford it.

**Metastable failure.** Sometimes the system stays down even after the trigger is gone. A brief database blip empties a cache, and the cold cache sends ten times the usual load to the database. Timeouts and retries keep that load above what the database can serve, so the cache never warms back up. The system is stable, in the wrong state, and only shedding load breaks the loop.

The common thread: **waiting** is what spreads failure. Every pattern below limits how long, how often, or how many callers wait on something that isn't working.

## Timeouts

Every network call needs a timeout. Many client libraries default to waiting forever, or for minutes, and a call without a timeout holds a thread, a connection, and memory for as long as the dependency takes to answer, which may be never.

There are several, and each guards against a different fault:

| Timeout | Guards against | Typical value |
|---|---|---|
| **Connect** | A host that's down or unreachable | Tens to hundreds of milliseconds inside a data center |
| **Request** (or read) | A server that accepted the request but is slow to respond | From the callee's latency percentiles |
| **Idle** | Connections left open with nothing happening | Seconds to minutes |
| **Overall deadline** | The whole operation, including retries | What the user will wait |

Choosing a request timeout is a trade-off. Too long, and resources stay tied up waiting on a sick dependency. Too short, and healthy-but-slow requests fail, and their retries add load. A good starting point is the callee's **p99 or p99.9 latency** plus a margin, measured in production (lesson 36). Systems that must detect failures quickly use **adaptive** timeouts that track observed response times, as TCP's retransmission timer and Cassandra's phi accrual failure detector do.

### Deadlines

Per-call timeouts aren't enough on their own. Suppose the gateway gives a request 1 second, and calls service A with a 1-second timeout. A calls B with its own 1-second timeout, and B calls C the same way. At 1 second, the gateway gives up and returns an error. But A, B, and C keep working for up to another second each, on a request nobody is waiting for. Under load, this **orphaned work** can be a large share of everything the system does.

A **deadline** fixes it by making the budget end to end:

1. The edge sets a deadline for the whole request: "this must finish within 1 second."
2. Each service computes its downstream call's timeout from the **time remaining**, minus a small margin to leave itself time to respond.
3. It passes the remaining time to the next hop along with the request.
4. Every service checks the deadline before starting expensive work, and drops requests whose deadline passed while they sat in a queue.

gRPC does this natively: a client deadline travels with the call as a `grpc-timeout` header, and every server in the chain sees how long it has left. Note that the header carries a **relative** duration ("250 ms left"), not an absolute timestamp ("finish by 12:00:00.250"). Each machine has its own clock, and they disagree (lesson 27), so an absolute deadline would be measured against the wrong clock. A duration only needs each machine's clock to measure elapsed time correctly, which monotonic clocks do well.

## Retries

Many faults are **transient**: a dropped packet, a server restarting during a deploy, a load balancer failing over. Retrying turns them into a little extra latency instead of an error. But retries are also the main way overload spreads, so they need rules.

**Retry only what can succeed, and only what's safe.**

- Retry **transient** errors: connection refused or reset, timeouts, `503 Service Unavailable`, `429 Too Many Requests` (after the `Retry-After` the server asked for).
- Don't retry **permanent** errors: `400 Bad Request`, `401`, `403`, `404`, validation failures. They'll fail the same way every time.
- Retry only **idempotent** operations (lesson 4), or ones carrying an idempotency key (lesson 32). A timed-out payment may already have gone through.

**Back off exponentially.** Wait longer after each failure: `base × 2^attempt`, capped at a maximum. With a base of 100 ms: 100, 200, 400, 800 ms. Each retry gives the dependency more time to recover, and puts less pressure on it.

**Add jitter.** Exponential backoff alone has a flaw: when a dependency hiccups, a thousand clients fail at the same moment, back off by the same amount, and retry at the same moment again, in synchronized waves (a **thundering herd**). Randomizing the wait breaks up the waves:

| Strategy | Wait before retry *n* | Effect |
|---|---|---|
| No jitter | `min(cap, base × 2^n)` | Clients retry in synchronized bursts |
| **Full jitter** | `random(0, min(cap, base × 2^n))` | Retries spread evenly over the whole window |
| Equal jitter | half the backoff, plus `random(0, half)` | Guarantees some minimum wait |
| Decorrelated jitter | `min(cap, random(base, previous × 3))` | Grows like backoff, without a fixed schedule |

Simulations by AWS found that full jitter does the least total work and finishes the clients soonest, which is why it's a common default.

**Retry at one layer.** To avoid multiplying attempts across a call chain, retry at a single layer, usually the one directly calling the failing dependency, and have every other layer fail fast.

**Cap retries with a budget.** Even well-behaved retries triple the load when a dependency fails completely and every request retries twice. A **retry budget** limits retries to a fraction of normal traffic, say 10% of requests plus a small fixed allowance so low-traffic clients can still retry. During a total outage, the dependency sees at most 1.1 times its usual load, not 3 times. Finagle, Envoy, and gRPC all support retry budgets.

### Hedged requests

Retries handle *failures*. **Hedged requests** attack *slowness*. If a read hasn't returned within, say, the 95th-percentile latency, send the same request to a second replica and take whichever answers first. In "The Tail at Scale," Google described how this sharply cuts tail latency while adding only about 5% more load, since only the slowest 5% of requests send a hedge. Like retries, it only works for idempotent requests.

## Circuit breakers

Retries keep trying a dependency. Sometimes the kindest thing to do is to stop. A **circuit breaker** wraps calls to a dependency and watches their outcomes, like the electrical breaker that cuts power before a fault starts a fire:

```text
            failures reach threshold              trial call fails
  CLOSED ─────────────────────────────▶ OPEN ◀───────────────────── HALF-OPEN
    ▲                                    │                              │
    │                                    └── reset timeout passes ─────▶│
    └──────────────────────────────── trial call succeeds ──────────────┘
```

| State | Calls | Moves on when |
|---|---|---|
| **Closed** | Pass through; failures are counted | Failures reach the threshold → open |
| **Open** | Rejected immediately, without calling the dependency | The reset timeout passes → half-open |
| **Half-open** | One trial call (or a few) is let through | The trial succeeds → closed; it fails → open again |

An open breaker helps on both sides. The failing dependency gets breathing room to recover, instead of a flood of requests and retries. And callers get an **instant** error instead of waiting for a timeout, so their threads are free for work that can succeed. That's how a breaker stops a cascade.

Production breakers refine the basic machine:

- **Failure rate over a window** instead of consecutive failures: open when more than 50% of the last 100 calls failed, but only once there are enough calls to judge.
- **Slow calls count as failures**: a dependency answering in 10 seconds is as bad as one that's down.
- **Fallbacks**: when the breaker is open, return a cached value, a default, or a degraded response instead of an error.
- **Scope**: a breaker per *host* ejects one bad instance (Envoy calls this **outlier detection**, the passive health checks of lesson 8). A breaker per *service* protects callers when the whole service is sick.

A breaker's open state is an error that retries must **not** retry: the point is that the dependency is known to be down. And tune the threshold with care. A breaker that trips on a brief blip turns a few failed requests into 30 seconds of total outage.

## Bulkheads

A ship's hull is divided into watertight compartments, called **bulkheads**, so one breach floods one compartment instead of sinking the ship. In software, a bulkhead **caps the resources one dependency can consume**, so a problem with that dependency can't use up everything.

Back to the cascading failure from the start of the lesson. With 200 shared worker threads, the slow recommendations service eventually holds all 200. With a bulkhead limiting recommendations to 20 concurrent calls, the 21st call is rejected instantly (and the page renders without recommendations), while the other 180 threads keep serving checkout. The fault stays in its compartment.

Bulkheads come in many sizes:

- **Per-dependency concurrency limits**: a semaphore or a separate connection pool for each downstream service.
- **Separate thread pools**: for blocking work against each dependency.
- **Separate instances for different traffic**: critical user requests on one pool of servers, batch jobs and internal tools on another.
- **Cells**: the whole system copied into independent cells, each serving a slice of customers, so a bad deploy or a poisonous request affects one cell's customers, not everyone's. **Shuffle sharding** assigns each customer a random small set of cells, so two customers rarely share all of theirs.

Size a concurrency limit with **Little's law**: the number of requests in progress equals throughput times latency. A dependency serving 100 requests a second at 200 ms needs about 20 concurrent slots, so a limit of 30 leaves headroom, while a limit of 200 offers no protection. **Adaptive concurrency limits** (as in Netflix's library of that name) adjust the limit automatically by watching latency, the way TCP congestion control adjusts its window.

## Load shedding and graceful degradation

Everything so far protects a *caller* from a failing dependency. The dependency needs to protect itself, too.

- **Load shedding**: when a server is overloaded (its queue too long, its latency too high), it rejects some requests immediately with `503` and a `Retry-After`, rather than accepting everything and serving all of it slowly. Rejecting a request costs microseconds; timing it out costs seconds of work that's thrown away. Shed **low-priority** traffic first (prefetches, analytics, batch jobs) and keep user-facing requests.
- **Bounded queues**: an unbounded queue turns overload into unbounded latency. A full queue should reject new work, which pushes back on the senders (**backpressure**).
- **Rate limiting** (lesson 22) caps each *client*. Load shedding caps the *server* at its own capacity, whoever is sending.
- **Graceful degradation**: serve stale data from a cache (`stale-if-error`, lesson 24), hide non-essential features, switch to read-only mode, or show a static page. A degraded answer is usually far better than no answer.

## Putting it together

For one outbound call, the patterns stack in a consistent order:

```text
deadline check ─▶ bulkhead slot ─▶ circuit breaker ─▶ timeout ─▶ call
       ▲                                                          │
       └──── retry with backoff + jitter, within budget ◀─────────┘ (transient failure)
                                    │
                                    └─▶ fallback when everything fails
```

| Fault | Pattern |
|---|---|
| A dependency hangs | Timeouts and deadlines |
| A transient blip | Retries with backoff and jitter |
| Retries overwhelming a struggling service | Retry budgets, retrying at one layer |
| A dependency that's down for a while | Circuit breaker, fallback |
| One slow dependency starving the rest | Bulkhead |
| More traffic than capacity | Load shedding, rate limiting, backpressure |
| Occasional slow replicas | Hedged requests |

Libraries like resilience4j and Polly implement these patterns in code, and service meshes (lesson 32) apply many of them in the network. Either way, they only work if they're tested: **chaos engineering** injects faults (killing instances, adding latency, cutting connections) on purpose, in staging and carefully in production, to check that a breaker opens, a fallback renders, and a timeout fires before users notice. Netflix's Chaos Monkey made the practice famous by randomly terminating production servers during business hours.

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
