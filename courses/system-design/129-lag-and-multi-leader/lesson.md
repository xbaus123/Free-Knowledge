# Replication Lag and Multi-Leader Replication

*Chapter 5 · Replication and Caching.*

## Replication lag

With asynchronous followers, a follower may be seconds behind the leader (**eventual consistency**). That causes real anomalies, each with a named guarantee that prevents it:

| Anomaly | Example | Guarantee |
|---|---|---|
| Not seeing your own write | You post a comment, reload, and it's gone (the read hit a stale follower) | **Read-your-writes**: read your own recent changes from the leader, or wait until the follower has caught up to your write |
| Time going backward | Refresh twice and see a comment appear, then disappear | **Monotonic reads**: always route a user to the same replica |
| Effects before causes | You see an answer before the question it replies to | **Consistent prefix reads**: see writes in the order they happened |

The replication lag readings later in this chapter take each of these guarantees apart, and you'll build them yourself.

## Multi-leader replication

Several nodes accept writes, each one a leader for some clients, and they replicate to each other. It's useful across **multiple data centers** (each has a local leader, so writes are fast and survive a data center outage; chapter 6), for **offline clients** (each device is a leader, as in calendar sync), and for **collaborative editing**.

The cost is **write conflicts**: two leaders accept conflicting changes to the same record at the same time. Resolutions:

- **Avoid conflicts**: route all writes for a record to one leader.
- **Last write wins (LWW)**: keep the write with the highest timestamp. It's simple, but it silently discards the other write, and clock skew makes "last" unreliable.
- **Merge**: keep both values for the application or user to resolve, or use data types that merge automatically (**CRDTs**: counters, sets, collaborative text).

Next, a short check on what you just read.
