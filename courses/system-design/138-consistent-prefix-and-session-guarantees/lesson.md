# Consistent Prefix Reads and Session Guarantees

*Chapter 5 · Replication and Caching.*

## Consistent prefix reads

The third anomaly is subtler. In a partitioned database (chapter 6), each partition has its own leader and replicates independently. Suppose a question is posted to one partition, and the answer, written afterward, goes to another. If an observer reads from followers, and the answer's partition happens to replicate faster, the observer sees the **answer before the question**: an effect without its cause.

```text
partition 1:  "Does anyone know when the store closes?"  ─── replicates slowly ───▶  observer sees it second
partition 2:  "At 9 tonight."                            ─ replicates quickly ─▶     observer sees it first
```

**Consistent prefix reads** guarantees that if a sequence of writes happens in some order, anyone reading them sees them in that order, without gaps: some *prefix* of the true history, never the history with pieces missing from the middle. Within a single partition with single-leader replication, that's free: the log is applied in order. Across partitions, there's no global order.

Solutions:

- **Keep causally related writes in one partition.** Put a conversation's messages in the partition of the conversation, not of the author. Often the best answer, though not always possible.
- **Track causal dependencies.** Each write records which earlier writes it depends on: the reply depends on the question. A reader holds back a write until everything it depends on is visible. This is **causal consistency**, the strongest consistency model that doesn't require coordination and stays available during network partitions. Tracking dependencies precisely takes metadata, and systems use **version vectors** or **hybrid logical clocks** to summarize it compactly.
- **Use a total order.** A consensus-based log (chapter 8) or a timestamp oracle orders every write in the database, at the cost of a coordination round trip.

## Session guarantees, formally

These guarantees come from research on the Bayou system at Xerox PARC in 1994, which defined four **session guarantees** for clients of eventually consistent replicas:

| Guarantee | Promise to a session | The anomaly it prevents |
|---|---|---|
| **Read your writes** | Reads reflect the session's own earlier writes | My edit disappeared |
| **Monotonic reads** | Reads never return an older state than an earlier read | The comment appeared, then vanished |
| **Writes follow reads** | A write is ordered after any write the session read before it | My reply was applied before the post I replied to |
| **Monotonic writes** | The session's writes are applied in the order it made them | My "delete" was applied before my "create" |

All four are about a *session*: one user's view, not the whole system's. That's what makes them cheap. They need only per-session metadata, like the positions you'll track, rather than coordination between replicas. Together, they add up to causal consistency for that session.

How they relate to the stronger models:

| Model | What every reader sees | Cost |
|---|---|---|
| **Eventual consistency** | Something, eventually the same thing | Nothing extra |
| **Session guarantees** | A view consistent with its own history | Per-session positions; sometimes a leader read or a wait |
| **Causal consistency** | Causes before effects, for everyone | Dependency tracking |
| **Bounded staleness** | Data at most *t* seconds or *k* versions old | Lag monitoring and routing (Azure Cosmos DB offers it directly) |
| **Linearizability** | The latest write, as if there were one copy | Coordination on every read (chapter 8) |

Choosing between them is a product decision as much as an engineering one. A like count that's two seconds stale harms nobody. A bank balance that goes backward will generate support calls. Many applications use read-your-writes and monotonic reads for user-facing pages, causal ordering for conversations, and linearizable reads only for the few operations that need them, like checking a username is free or a seat is still available.

Next, a short check on what you just read.
