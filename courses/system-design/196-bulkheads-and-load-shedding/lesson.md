# Bulkheads, Load Shedding, and Putting It Together

*Chapter 7 · Transactions and Fault Tolerance.*

## Bulkheads

A ship's hull is divided into watertight compartments, called **bulkheads**, so one breach floods one compartment instead of sinking the ship. In software, a bulkhead **caps the resources one dependency can consume**, so a problem with that dependency can't use up everything.

Back to the cascading failure from the first resiliency reading. With 200 shared worker threads, the slow recommendations service eventually holds all 200. With a bulkhead limiting recommendations to 20 concurrent calls, the 21st call is rejected instantly (and the page renders without recommendations), while the other 180 threads keep serving checkout. The fault stays in its compartment.

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
- **Rate limiting** (chapter 6) caps each *client*. Load shedding caps the *server* at its own capacity, whoever is sending.
- **Graceful degradation**: serve stale data from a cache (`stale-if-error`, chapter 6), hide non-essential features, switch to read-only mode, or show a static page. A degraded answer is usually far better than no answer.

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

Libraries like resilience4j and Polly implement these patterns in code, and service meshes (chapter 9) apply many of them in the network. Either way, they only work if they're tested: **chaos engineering** injects faults (killing instances, adding latency, cutting connections) on purpose, in staging and carefully in production, to check that a breaker opens, a fallback renders, and a timeout fires before users notice. Netflix's Chaos Monkey made the practice famous by randomly terminating production servers during business hours.

Next, a short check on what you just read.
