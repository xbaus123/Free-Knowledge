# Monolith or Microservices

*Chapter 9 · Microservices and Data Flow.*

*Based on* Designing Data-Intensive Applications*, Chapters 9 and 12.*

*Based on* Designing Data-Intensive Applications*, Chapters 9 and 12.*

The last chapter showed how hard it is for a handful of nodes to agree on anything: who the leader is, whether a lock is still held, whether a transaction committed. Microservices take one application and deliberately split it into dozens or hundreds of processes that must cooperate over the network. Teams do this anyway, for good reasons, and pay for it with every problem from Part II. The microservices readings cover when the trade is worth it, where to draw the lines between services, how a service mesh handles the network for them, and how to keep data consistent across services that each own their own database.

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

Next, a short check on what you just read.
