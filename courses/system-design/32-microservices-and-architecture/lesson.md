# Microservices: Boundaries, Service Meshes, and Sagas

*Based on* Designing Data-Intensive Applications*, Chapters 9 and 12.*

The last few lessons showed how hard it is for a handful of nodes to agree on anything: who the leader is, whether a lock is still held, whether a transaction committed. Microservices take one application and deliberately split it into dozens or hundreds of processes that must cooperate over the network. Teams do this anyway, for good reasons, and pay for it with every problem from Part II. This lesson covers when the trade is worth it, where to draw the lines between services, how a service mesh handles the network for them, and how to keep data consistent across services that each own their own database.

## Monolith or microservices

A **monolith** is one deployable unit: one codebase, one build, one process type (scaled out behind a load balancer), usually one database. A **microservice architecture** splits the system into small services, each **independently deployable**, each **owning its data**, talking to the others only through APIs and events.

| | Monolith | Microservices |
|---|---|---|
| **Calls between components** | Function calls: nanoseconds, never lost | Network calls: milliseconds, can fail, time out, or run twice |
| **Transactions** | One ACID database transaction | Each service has its own database; cross-service consistency needs sagas |
| **Deploys** | Everything ships together; one bad change blocks everyone | Each team ships on its own schedule |
| **Scaling** | Scale the whole thing | Scale the hot service alone, on hardware that suits it |
| **Fault isolation** | A memory leak in reporting takes down checkout | A crashed recommendations service leaves checkout working, if you designed for it |
| **Teams** | Coordination cost grows with headcount | Teams own services end to end |
| **Operations** | One thing to deploy, monitor, and debug | Service discovery, tracing, per-service pipelines, versioned APIs |
| **Refactoring across boundaries** | Rename a function and the compiler finds every caller | Change an API, and every consumer must migrate |

The honest summary: **microservices mostly solve an organizational problem**. When 300 engineers share one codebase and one deploy pipeline, they block each other constantly. Splitting the system along team lines lets each team move independently. **Conway's law** observes that systems end up mirroring the communication structure of the organizations that build them, and the "inverse Conway maneuver" designs the team structure to get the architecture you want.

For a small team, those benefits barely exist, and the costs arrive on day one. The usual advice is to start with a **modular monolith**: one deployable, but with strict internal module boundaries, each module owning its own tables and exposing an interface. When a module genuinely needs independent scaling or an independent team, extract it. The boundaries are already there.

The worst outcome is the **distributed monolith**: services that must be deployed together, share a database, or can't serve a request without calling five others synchronously. It has all the costs of microservices and none of the benefits. Teams have gone both ways: Segment publicly moved over a hundred services back into one, and Amazon Prime Video collapsed one distributed monitoring pipeline into a single process and cut its cost by 90%.

## Finding boundaries: Domain-Driven Design

Where you cut matters more than whether you cut. Cut in the wrong place, and every feature touches four services and every request crosses the network ten times. **Domain-Driven Design (DDD)**, from Eric Evans's 2003 book, gives the vocabulary for finding good boundaries.

### Bounded contexts

In a large business, the same word means different things to different people. To sales, a **customer** is a lead with a pipeline stage. To billing, it's a payment method and an invoice history. To support, it's a ticket history and a satisfaction score. A **product** in the catalog has photos and descriptions. In the warehouse, it has a shelf location and a weight.

Trying to build one `Customer` model for everyone produces a giant, fragile class that every team must change. DDD instead defines **bounded contexts**: areas of the business with their own consistent model and their own **ubiquitous language** (the shared vocabulary of that context's domain experts and engineers). Each context has its own `Customer`, holding only what it needs, linked to the others by a shared id. **A bounded context is the natural boundary for a service**, or for a small group of services owned by one team.

### Aggregates

Inside a context, an **aggregate** is a cluster of objects that must stay consistent together, with one **root** that all changes go through. An `Order` with its line items is an aggregate: the total must always match the items. DDD's rules:

- A transaction modifies **one aggregate**.
- Aggregates refer to each other **by id**, not by object reference.
- Consistency *between* aggregates is **eventual**, through events.

These rules are what make splitting possible. If no transaction ever spans two aggregates, aggregates can live in different databases, or different services, without distributed transactions.

### Good boundaries

- **Split by business capability** (ordering, payments, inventory, shipping), not by technical layer. A "database service" or a "validation service" that every other service calls is a bottleneck in disguise.
- **High cohesion, low coupling**: things that change together stay together. If every feature needs coordinated changes to two services, they're one service.
- **Database per service**: each service owns its tables, and nobody else reads them directly. A shared database is hidden coupling: one team's schema change breaks another's queries, and nobody can tell who depends on what. Data needed elsewhere is shared through APIs, or published as **events** that other services use to build their own **derived** read models (lessons 34 and 35).
- **Translate at the edges**: when your context consumes another's model (especially a legacy system or a vendor), wrap it in an **anti-corruption layer** that translates their concepts into yours, so their quirks don't leak through your code.

To migrate a monolith, use the **strangler fig** pattern (named after a vine that grows around a tree until it replaces it): put a proxy (lesson 8) in front of the monolith, then route one capability at a time to new services, until nothing is left.

## Communication and its failure modes

Services talk in two styles:

- **Synchronous** request/response (REST or gRPC, lesson 4): simple to reason about, but the caller waits, and it fails if the callee fails. The services are **coupled in time**.
- **Asynchronous** events or messages through a broker (lesson 33): the producer moves on, and consumers process when they can. Services stay up when their neighbors are down, at the cost of **eventual consistency** and harder debugging.

### Availability multiplies

If a request needs services A, B, and C to all be up, and each is up 99.9% of the time independently, the request succeeds only 99.9% × 99.9% × 99.9% ≈ 99.7% of the time. With 10 synchronous dependencies, it's 99.0%: about 7 hours of failures a month instead of 43 minutes. Latency adds up the same way along a chain, and fan-out amplifies tail latency (lesson 1).

So minimize **synchronous** dependencies on the critical path. Cache what you can. Make non-essential dependencies optional: if recommendations are down, show the page without them (**graceful degradation**). Move work that doesn't need to finish before the response behind a queue.

**Cycles** in the synchronous call graph are worse. If A calls B and B calls A, neither can be deployed or scaled on its own, a slowdown in either feeds back into both, and retries circle around until both are overloaded. A cycle is a sign that two services are really one, or that one direction of the call should be an event.

### Resilience patterns

Every remote call needs a plan for failure, and lesson 28 built the toolkit: **timeouts** and propagated **deadlines**, **retries** with backoff, jitter, and a budget (and only for idempotent operations), **circuit breakers** that stop calling a dependency that keeps failing, and **bulkheads** that keep one slow dependency from using up every thread. In a microservice architecture they stop being optional. With dozens of services, some dependency is always degraded, and these patterns are what keep that from spreading through the call graph. The question is where to put them: in a library inside every service, or in the network.

## Service mesh

Every service needs the same networking features: service discovery, load balancing, timeouts, retries, circuit breakers, mTLS (lesson 9), metrics, and tracing (lesson 36). Building them into a library works until your services are written in five languages, each needing its own version, upgraded in lockstep.

A **service mesh** moves those features out of the application into the network:

- The **data plane** is a **sidecar proxy**, usually Envoy, deployed next to every service instance. All of the instance's inbound and outbound traffic flows through it. The application calls `http://payments/charge` in plain HTTP, and the sidecar finds a healthy payments instance, opens an mTLS connection to *its* sidecar, applies timeouts and retries, and records metrics and trace spans.
- The **control plane** (Istio, Linkerd, Consul) configures every sidecar: routing rules, retry policies, which services may call which, and short-lived certificates for every workload's identity.

This gives you uniform behavior across languages, encryption and identity everywhere, and changes like "send 5% of traffic to v2" (**traffic shifting**, for canary releases) without touching application code. It's the client-side load balancing of lesson 8, done for every service at once. The costs: an extra proxy hop on every call (typically under a millisecond each way), CPU and memory for thousands of proxies, and a complex system of its own to operate. Newer "sidecarless" designs move the proxy into a shared per-node agent, or into the kernel with eBPF, to cut that overhead.

A mesh can't fix bad boundaries. And a mesh retrying a non-idempotent call still charges the customer twice.

## Transactions across services: sagas

Placing an order touches four services, each with its own database: **orders** records it, **inventory** reserves the items, **payments** charges the card, and **shipping** books a courier. In a monolith, that's one ACID transaction. Across services, there isn't one.

**Two-phase commit** (lesson 30) can do it in principle, but it's a poor fit: it requires every participant to support the same distributed transaction protocol, it holds locks in every service while the slowest one votes, and when the coordinator fails, participants are stuck holding locks. Availability multiplies here too, so 2PC across services is rarely used.

A **saga** (from a 1987 paper by Hector Garcia-Molina and Kenneth Salem) gives up atomic isolation for availability. A saga is a sequence of **local transactions**, one per service, each committed on its own. Each step has a **compensating transaction** that semantically undoes it. If step *k* fails, the saga runs the compensations for steps *k − 1* down to 1, in reverse order:

```text
reserve items ──▶ charge card ──▶ book courier ✗
                                       │
release items ◀── refund card ◀────────┘
```

### Compensation isn't rollback

A database rollback makes it as if the transaction never happened. A compensation is a new action with its own visible effects: a refund appears on the customer's statement next to the charge, and a cancelled shipment may still have a cancellation fee. Some actions can't be compensated at all: you can't un-send an email or un-launch a rocket. So **order the steps carefully**:

- Put steps that are easy to undo, or likely to fail (validation, reservations), **first**.
- Put irreversible steps (sending notifications, dispatching goods) **last**, after the saga can no longer fail.
- The step after which the saga is guaranteed to complete is the **pivot**. Steps after it must be **retriable**: they're retried until they succeed, never compensated.

### Orchestration versus choreography

| | Orchestration | Choreography |
|---|---|---|
| **How** | A central **orchestrator** tells each service what to do next and tracks the saga's state | Each service listens for events and reacts: `OrderPlaced` → inventory reserves → `ItemsReserved` → payments charges |
| **Visibility** | The whole flow is in one place, with one state per saga | The flow is spread across services; you reconstruct it from events and traces |
| **Coupling** | Services depend on the orchestrator's commands | Services depend on each other's events |
| **Good for** | Complex flows with many steps and branches | Simple flows of a few steps |
| **Tools** | Temporal, AWS Step Functions, Camunda | A message broker (lesson 33) |

Choreography looks more decoupled, but in a long flow, nobody can answer "what happens after an order is placed?" without reading every service, and event cycles creep in. Most teams orchestrate sagas of more than three or four steps.

### Sagas lack isolation

A saga is atomic (eventually), consistent, and durable, but not **isolated**. Other requests see its intermediate states: a product shows as out of stock because a saga reserved the last one, and then the saga is compensated and the stock comes back. These are the dirty reads and lost updates of lesson 25, now across services. Countermeasures:

- **Semantic locks**: mark records as `PENDING` while a saga runs, so others know to wait or treat them specially.
- **Commutative updates**: design operations that give the same result in any order (`add 5 to balance` rather than `set balance to 105`).
- **Reread before acting**: check that a value hasn't changed before relying on it.

### Making sagas survive crashes

The orchestrator itself can crash at any moment: after charging the card but before recording that it did. Three techniques, which DDIA's final chapter argues apply to any system built from many components, make sagas reliable:

1. **A durable saga log.** The orchestrator records each step's outcome in durable storage before moving on. When it crashes, another instance reads the log and **resumes** where it stopped. Temporal records every step of a workflow this way and replays the history to resume it.
2. **Idempotency keys.** After a crash, the orchestrator can't know whether the in-flight step ran, so it runs it again. Each call carries an **idempotency key** (such as `order-7/charge`), and the participant stores the keys it has processed **in the same local transaction** as the effect. A repeated key returns the stored result instead of charging twice. DDIA calls this the **end-to-end argument**: only an id that travels with the request from end to end can suppress duplicates reliably, because every layer in between (TCP, the broker, the retrying client) can fail and retry on its own.
3. **The transactional outbox.** A service that updates its database *and* publishes an event has a dual-write problem: either can fail without the other. Instead, write the event into an `outbox` table in the **same** local transaction as the change, and let a separate relay publish the outbox to the broker, often with change data capture (lesson 35).

Compensations need the same care: they must be idempotent and retried until they succeed. If one keeps failing (the payment provider rejects every refund), the saga is **stuck**, and a human must step in. A good orchestrator surfaces stuck sagas loudly rather than skipping ahead.

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
