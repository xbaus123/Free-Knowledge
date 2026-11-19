# Timeouts and Deadlines

*Chapter 7 · Transactions and Fault Tolerance.*

## Timeouts

Every network call needs a timeout. Many client libraries default to waiting forever, or for minutes, and a call without a timeout holds a thread, a connection, and memory for as long as the dependency takes to answer, which may be never.

There are several, and each guards against a different fault:

| Timeout | Guards against | Typical value |
|---|---|---|
| **Connect** | A host that's down or unreachable | Tens to hundreds of milliseconds inside a data center |
| **Request** (or read) | A server that accepted the request but is slow to respond | From the callee's latency percentiles |
| **Idle** | Connections left open with nothing happening | Seconds to minutes |
| **Overall deadline** | The whole operation, including retries | What the user will wait |

Choosing a request timeout is a trade-off. Too long, and resources stay tied up waiting on a sick dependency. Too short, and healthy-but-slow requests fail, and their retries add load. A good starting point is the callee's **p99 or p99.9 latency** plus a margin, measured in production (chapter 10). Systems that must detect failures quickly use **adaptive** timeouts that track observed response times, as TCP's retransmission timer and Cassandra's phi accrual failure detector do.

### Deadlines

Per-call timeouts aren't enough on their own. Suppose the gateway gives a request 1 second, and calls service A with a 1-second timeout. A calls B with its own 1-second timeout, and B calls C the same way. At 1 second, the gateway gives up and returns an error. But A, B, and C keep working for up to another second each, on a request nobody is waiting for. Under load, this **orphaned work** can be a large share of everything the system does.

A **deadline** fixes it by making the budget end to end:

1. The edge sets a deadline for the whole request: "this must finish within 1 second."
2. Each service computes its downstream call's timeout from the **time remaining**, minus a small margin to leave itself time to respond.
3. It passes the remaining time to the next hop along with the request.
4. Every service checks the deadline before starting expensive work, and drops requests whose deadline passed while they sat in a queue.

gRPC does this natively: a client deadline travels with the call as a `grpc-timeout` header, and every server in the chain sees how long it has left. Note that the header carries a **relative** duration ("250 ms left"), not an absolute timestamp ("finish by 12:00:00.250"). Each machine has its own clock, and they disagree (earlier in this chapter), so an absolute deadline would be measured against the wrong clock. A duration only needs each machine's clock to measure elapsed time correctly, which monotonic clocks do well.

Next, a short check on what you just read.
