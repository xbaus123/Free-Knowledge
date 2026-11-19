# Replication: Single Leader

*Chapter 5 · Replication and Caching.*

*Based on* Designing Data-Intensive Applications*, Chapter 5.*

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

In practice, systems often make one follower synchronous and the rest asynchronous (**semi-synchronous**). You saw this trade-off in chapter 2: a sync standby added 4 ms per write, and an async one lost recent writes on failover.

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

Next, a short check on what you just read.
