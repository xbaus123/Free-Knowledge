# Sagas: Transactions Across Services

*Chapter 9 · Microservices and Data Flow.*

## Transactions across services: sagas

Placing an order touches four services, each with its own database: **orders** records it, **inventory** reserves the items, **payments** charges the card, and **shipping** books a courier. In a monolith, that's one ACID transaction. Across services, there isn't one.

**Two-phase commit** (chapter 8) can do it in principle, but it's a poor fit: it requires every participant to support the same distributed transaction protocol, it holds locks in every service while the slowest one votes, and when the coordinator fails, participants are stuck holding locks. Availability multiplies here too, so 2PC across services is rarely used.

A **saga** (from a 1987 paper by Hector Garcia-Molina and Kenneth Salem) gives up atomic isolation for availability. A saga is a sequence of **local transactions**, one per service, each committed on its own. Each step has a **compensating transaction** that semantically undoes it. If step *k* fails, the saga runs the compensations for steps *k − 1* down to 1, in reverse order:

```text
reserve items ──▶ charge card ──▶ book courier ✗
                                       │
release items ◀── refund card ◀────────┘
```

## Compensation isn't rollback

A database rollback makes it as if the transaction never happened. A compensation is a new action with its own visible effects: a refund appears on the customer's statement next to the charge, and a cancelled shipment may still have a cancellation fee. Some actions can't be compensated at all: you can't un-send an email or un-launch a rocket. So **order the steps carefully**:

- Put steps that are easy to undo, or likely to fail (validation, reservations), **first**.
- Put irreversible steps (sending notifications, dispatching goods) **last**, after the saga can no longer fail.
- The step after which the saga is guaranteed to complete is the **pivot**. Steps after it must be **retriable**: they're retried until they succeed, never compensated.

## Orchestration versus choreography

| | Orchestration | Choreography |
|---|---|---|
| **How** | A central **orchestrator** tells each service what to do next and tracks the saga's state | Each service listens for events and reacts: `OrderPlaced` → inventory reserves → `ItemsReserved` → payments charges |
| **Visibility** | The whole flow is in one place, with one state per saga | The flow is spread across services; you reconstruct it from events and traces |
| **Coupling** | Services depend on the orchestrator's commands | Services depend on each other's events |
| **Good for** | Complex flows with many steps and branches | Simple flows of a few steps |
| **Tools** | Temporal, AWS Step Functions, Camunda | A message broker (later in this chapter) |

Choreography looks more decoupled, but in a long flow, nobody can answer "what happens after an order is placed?" without reading every service, and event cycles creep in. Most teams orchestrate sagas of more than three or four steps.

Next, a short check on what you just read.
