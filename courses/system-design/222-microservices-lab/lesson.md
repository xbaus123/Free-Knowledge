# Microservices: Boundaries, Service Meshes, and Sagas

*Chapter 9 · Microservices and Data Flow.*

Build what the microservices readings described: dependency analysis of a service call graph, and a crash-safe saga orchestrator.

## Your task

`solution.py` has two parts.

### 1. Dependency analysis

`graph` maps each service to the list of services it calls synchronously.

- `find_cycle(graph)` returns one cycle as a list that starts and ends with the same service, like `["cart", "pricing", "discounts", "cart"]`, or `None` if there is none. Use a depth-first search that tracks which services are on the current path: reaching one of them again closes a cycle. A service reached twice by different paths (a diamond) is not a cycle.
- `availability(graph, slo, service)` returns the product of the availabilities in `slo` of `service` and every service it depends on **directly or indirectly**, each counted **once**, even if several paths lead to it or the graph has cycles.

### 2. Sagas

- `IdempotencyStore.run(key, fn)` runs `fn()` the first time it sees `key` and remembers its result. Later calls with that key return the remembered result without running `fn`. If `fn` raises, remember nothing, so it can be retried.
- `Saga(steps, log, max_retries).run(saga_id, ctx)` runs each `Step`'s `action(ctx, key)` in order, where `key` is `f"{saga_id}/{step.name}"`. `log` is a list standing in for durable storage, shared with other orchestrator processes. Append events to it as tuples:
  - `(saga_id, step.name, "done")` after each action succeeds, and `(saga_id, None, "completed")` once all of them have.
  - If an action raises an `Exception`, log `(saga_id, step.name, "failed")`, then run the compensations of the completed steps in reverse order, each as `compensation(ctx, key)` with that step's key. Retry each compensation up to `max_retries` times in total, logging `(saga_id, step.name, "compensated")` once it succeeds. Finish with `(saga_id, None, "compensated")`. If a compensation fails every attempt, log `(saga_id, None, "stuck")` and stop.
  - Return the final status: `"completed"`, `"compensated"`, or `"stuck"`.
- `run` must also **resume** a saga from the log. The tests simulate an orchestrator crash by raising `Crash` from inside a step. `Crash` is a `BaseException`, not an `Exception`, so `except Exception` won't catch it, and it ends `run` immediately. A new `Saga` with the same log then calls `run` again for the same `saga_id`:
  - If the log already holds that saga's final status, return it without running anything.
  - Skip steps already logged as `done`. A step that was in flight during the crash isn't logged, so it runs again, with the same key.
  - If the log holds a `failed` event for the saga, go straight to compensating, skipping compensations already logged.
  - Read only the events whose `saga_id` matches: many sagas share one log.

Try a saga in the **Scratchpad**:

```python
from solution import Saga, Step

def say(msg):
    return lambda ctx, key: print(msg, key)

def fail(ctx, key):
    raise RuntimeError("card declined")

steps = [Step("reserve", say("reserved"), say("released")), Step("charge", fail, say("refunded"))]
log = []
print(Saga(steps, log).run("order-1", {}), log)
```

## Think about it

- Your saga retries the in-flight step after a crash. Which real-world participants make that dangerous without idempotency keys? Where does the payment service store its keys, and why must it be the same transaction as the charge?
- Sketch the bounded contexts of a food delivery app. Which word means something different in each of them?
- A service mesh retries failed calls automatically, and so does your HTTP client library, and so does the mobile app. What happens during an outage of the deepest service?

## Key terms

| Term | Meaning |
|---|---|
| Modular monolith | One deployable with strict internal module boundaries |
| Distributed monolith | Services so coupled they must change and deploy together |
| Conway's law | Systems mirror the communication structure of the organizations that build them |
| Bounded context | A part of the domain with its own consistent model and language |
| Aggregate | A cluster of objects kept consistent together, changed in one transaction |
| Anti-corruption layer | A translation layer that keeps another model's concepts out of yours |
| Strangler fig | Replacing a system piece by piece behind a routing proxy |
| Service mesh | Sidecar proxies (data plane) configured centrally (control plane) |
| Saga | A sequence of local transactions with compensations for failure |
| Compensating transaction | A new action that semantically undoes an earlier step |
| Orchestration / choreography | A central coordinator directs the saga / services react to each other's events |
| Pivot transaction | The step after which a saga must run to completion |
| Idempotency key | A request id that lets the receiver recognize and ignore duplicates |
| Transactional outbox | Writing outgoing events in the same transaction as the change they describe |
