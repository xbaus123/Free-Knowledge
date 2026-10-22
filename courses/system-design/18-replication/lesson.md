# Replication: Leaders, Followers, and Quorums

*Part II · Distributed Data. Based on* Designing Data-Intensive Applications*, Chapter 5.*

**Replication** means keeping a copy of the same data on several machines connected by a network. You do it to:

- **Stay available** when a machine fails.
- **Scale reads** by spreading them over many copies.
- **Reduce latency** by keeping a copy close to users.

Replicating data that never changes is easy. All the difficulty is in handling **changes**. There are three main approaches.

## Single-leader replication

One replica is the **leader** (primary). All writes go to it. It sends each change to the **followers** (replicas, secondaries) through a **replication log**, and they apply the changes in the same order. Reads can go to any replica. PostgreSQL, MySQL, MongoDB, and Kafka all work this way.

### Synchronous vs. asynchronous

- **Synchronous**: the leader waits until a follower confirms before telling the client the write succeeded. That follower is guaranteed up to date, but if it's slow or down, writes stall.
- **Asynchronous**: the leader confirms immediately and replicates in the background. It's fast, but if the leader dies, confirmed writes that hadn't reached a follower are **lost**.

In practice, systems often make one follower synchronous and the rest asynchronous (**semi-synchronous**). You saw this trade-off in lesson 7: a sync standby added 4 ms per write, and an async one lost recent writes on failover.

### Handling failures

- **A follower fails**: when it comes back, it asks the leader for every change since the last one it applied, and catches up.
- **The leader fails**: you need **failover**. Detect that the leader is dead (usually a timeout), choose a new leader (the most up-to-date follower), and point clients and followers at it. Every step can go wrong:
  - With async replication, the new leader may be missing writes. Those writes are usually discarded, which is dangerous if other systems already saw them. At GitHub, an out-of-date MySQL follower was promoted and reused auto-increment ids that were also stored in Redis, leaking private data to the wrong users.
  - **Split brain**: two nodes both believe they're the leader and both accept writes.
  - Too short a timeout causes needless failovers during load spikes. Too long, and recovery is slow.

### Replication logs

- **Statement-based**: send the SQL statements. This breaks on nondeterministic functions like `NOW()` or `RAND()`.
- **Write-ahead log shipping**: send the storage engine's low-level log. It's exact, but tied to one storage format and version.
- **Logical (row-based) log**: send which rows changed and how. It's decoupled from storage internals, and it's the basis for **change data capture**, which you'll use in Part III.

## Replication lag

With asynchronous followers, a follower may be seconds behind the leader (**eventual consistency**). That causes real anomalies, each with a named guarantee that prevents it:

| Anomaly | Example | Guarantee |
|---|---|---|
| Not seeing your own write | You post a comment, reload, and it's gone (the read hit a stale follower) | **Read-your-writes**: read your own recent changes from the leader, or wait until the follower has caught up to your write |
| Time going backward | Refresh twice and see a comment appear, then disappear | **Monotonic reads**: always route a user to the same replica |
| Effects before causes | You see an answer before the question it replies to | **Consistent prefix reads**: see writes in the order they happened |

In lesson 19, you'll fight a lagging replica in the simulator.

## Multi-leader replication

Several nodes accept writes, each one a leader for some clients, and they replicate to each other. It's useful across **multiple data centers** (each has a local leader, so writes are fast and survive a data center outage; lesson 23), for **offline clients** (each device is a leader, as in calendar sync), and for **collaborative editing**.

The cost is **write conflicts**: two leaders accept conflicting changes to the same record at the same time. Resolutions:

- **Avoid conflicts**: route all writes for a record to one leader.
- **Last write wins (LWW)**: keep the write with the highest timestamp. It's simple, but it silently discards the other write, and clock skew makes "last" unreliable.
- **Merge**: keep both values for the application or user to resolve, or use data types that merge automatically (**CRDTs**: counters, sets, collaborative text).

## Leaderless replication

Any replica accepts writes. The client, or a coordinator, sends each write to **all n replicas** and each read to several. This is the style of Amazon's Dynamo, Cassandra, and Riak.

### Quorum math

- **n** = number of replicas
- **w** = replicas that must confirm a write
- **r** = replicas that must answer a read

If **w + r > n**, the replicas you write to and the replicas you read from must **overlap** in at least one node. So every read sees at least one copy of the latest successful write, and version numbers tell the client which copy is newest.

| n | w | r | w + r > n? | Tolerates |
|---|---|---|---|---|
| 3 | 2 | 2 | 4 > 3 ✓ | 1 node down for reads and writes |
| 5 | 3 | 3 | 6 > 5 ✓ | 2 nodes down |
| 3 | 3 | 1 | 4 > 3 ✓ | Fast reads, but one node down blocks writes |
| 3 | 1 | 1 | 2 ≤ 3 ✗ | Stale reads possible |

A common choice is n odd and w = r = (n + 1) / 2, a **majority**.

### Keeping replicas in sync

- **Read repair**: when a read sees a stale copy on some replica, the client writes the newer value back to it.
- **Anti-entropy**: a background process compares replicas and copies missing data.

### Edge cases

Even with w + r > n, quorums aren't a hard guarantee:

- **Sloppy quorums** with **hinted handoff** accept writes on other nodes during a network partition, so the overlap no longer holds.
- Concurrent writes still conflict.
- A write that failed on some replicas isn't rolled back on the others.

Quorums make stale reads *unlikely*, not impossible. For guarantees, you'll need the consensus algorithms of Part II's final chapter.

## Key terms

| Term | Meaning |
|---|---|
| Leader / follower | The replica that takes writes / replicas that copy it |
| Synchronous / asynchronous | Wait for the replica's confirmation / don't wait |
| Failover | Promoting a follower when the leader dies |
| Split brain | Two nodes both acting as leader |
| Replication lag | How far a follower trails the leader |
| Read-your-writes | Users always see their own changes |
| LWW | Last write wins: discard all but the latest timestamp |
| Quorum (w + r > n) | Write and read sets overlap, so reads see the latest write |
