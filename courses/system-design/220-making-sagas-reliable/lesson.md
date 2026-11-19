# Saga Isolation and Crash Safety

*Chapter 9 · Microservices and Data Flow.*

## Sagas lack isolation

A saga is atomic (eventually), consistent, and durable, but not **isolated**. Other requests see its intermediate states: a product shows as out of stock because a saga reserved the last one, and then the saga is compensated and the stock comes back. These are the dirty reads and lost updates of chapter 7, now across services. Countermeasures:

- **Semantic locks**: mark records as `PENDING` while a saga runs, so others know to wait or treat them specially.
- **Commutative updates**: design operations that give the same result in any order (`add 5 to balance` rather than `set balance to 105`).
- **Reread before acting**: check that a value hasn't changed before relying on it.

## Making sagas survive crashes

The orchestrator itself can crash at any moment: after charging the card but before recording that it did. Three techniques, which DDIA's final chapter argues apply to any system built from many components, make sagas reliable:

1. **A durable saga log.** The orchestrator records each step's outcome in durable storage before moving on. When it crashes, another instance reads the log and **resumes** where it stopped. Temporal records every step of a workflow this way and replays the history to resume it.
2. **Idempotency keys.** After a crash, the orchestrator can't know whether the in-flight step ran, so it runs it again. Each call carries an **idempotency key** (such as `order-7/charge`), and the participant stores the keys it has processed **in the same local transaction** as the effect. A repeated key returns the stored result instead of charging twice. DDIA calls this the **end-to-end argument**: only an id that travels with the request from end to end can suppress duplicates reliably, because every layer in between (TCP, the broker, the retrying client) can fail and retry on its own.
3. **The transactional outbox.** A service that updates its database *and* publishes an event has a dual-write problem: either can fail without the other. Instead, write the event into an `outbox` table in the **same** local transaction as the change, and let a separate relay publish the outbox to the broker, often with change data capture (later in this chapter).

Compensations need the same care: they must be idempotent and retried until they succeed. If one keeps failing (the payment provider rejects every refund), the saga is **stuck**, and a human must step in. A good orchestrator surfaces stuck sagas loudly rather than skipping ahead.

Next, a short check on what you just read.
