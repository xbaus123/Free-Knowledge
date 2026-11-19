# Retries, Backoff, and Jitter

*Chapter 7 · Transactions and Fault Tolerance.*

## Retries

Many faults are **transient**: a dropped packet, a server restarting during a deploy, a load balancer failing over. Retrying turns them into a little extra latency instead of an error. But retries are also the main way overload spreads, so they need rules.

**Retry only what can succeed, and only what's safe.**

- Retry **transient** errors: connection refused or reset, timeouts, `503 Service Unavailable`, `429 Too Many Requests` (after the `Retry-After` the server asked for).
- Don't retry **permanent** errors: `400 Bad Request`, `401`, `403`, `404`, validation failures. They'll fail the same way every time.
- Retry only **idempotent** operations (chapter 1), or ones carrying an idempotency key (chapter 9). A timed-out payment may already have gone through.

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

Next, a short check on what you just read.
