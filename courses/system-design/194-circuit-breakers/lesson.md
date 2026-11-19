# Circuit Breakers

*Chapter 7 · Transactions and Fault Tolerance.*

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
- **Scope**: a breaker per *host* ejects one bad instance (Envoy calls this **outlier detection**, the passive health checks of chapter 2). A breaker per *service* protects callers when the whole service is sick.

A breaker's open state is an error that retries must **not** retry: the point is that the dependency is known to be down. And tune the threshold with care. A breaker that trips on a brief blip turns a few failed requests into 30 seconds of total outage.

Next, a short check on what you just read.
