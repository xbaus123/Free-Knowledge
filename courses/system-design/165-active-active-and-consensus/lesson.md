# Active-Active, Global Consensus, and CRDTs

*Chapter 6 · Partitioning and Geography.*

## Multi-leader active-active

Every region accepts writes and replicates them asynchronously to the others. DDIA calls this **multi-leader replication** and notes that multiple data centers are its main use case. Each region tolerates the loss of the others and keeps writes fast. But two regions can accept conflicting writes to the same record at the same time, and neither knows until replication delivers the other's version. Something must **resolve the conflict**:

- **Last write wins (LWW)**: keep the write with the latest timestamp. It's simple, and it silently **discards** data: two people liking a post at the same time in two regions, each writing `likes = 101`, leaves 101, not 102. And it trusts timestamps from clocks that disagree (chapter 7).
- **Conflict-free replicated data types (CRDTs)**: data structures whose replicas can be updated independently and **merged** in any order, any number of times, always converging to the same result. You'll build one below.
- **Application-level merge**: keep every conflicting version (as **siblings**) and let application code or the user combine them, as a shopping cart might take the union of items.

Cassandra and DynamoDB global tables run active-active across regions. Cassandra lets each request choose `LOCAL_QUORUM` (a quorum of replicas in the local region: fast, but another region may briefly disagree) or `EACH_QUORUM` (a quorum in every region: consistent, but as slow as the farthest one).

## Global consensus

Google Spanner and CockroachDB run consensus (chapter 8) for each partition, with replicas in several regions. A write commits once a majority has it, so losing one region loses nothing, and reads can be linearizable. The cost is physics: every write waits for a round trip to the nearest majority. With replicas in Virginia, Oregon, and Iowa, that's tens of milliseconds. Spanner goes further and uses its **TrueTime** clock API, backed by GPS receivers and atomic clocks, to give transactions globally meaningful timestamps.

This is the latency half of the **PACELC** trade-off: even when there's no network partition (the "else" case), a geo-distributed system chooses between low latency and strong consistency. Most designs choose differently for different data. A bank balance gets consensus. A like count gets a CRDT.

## CRDT counters

A counter shows the CRDT idea clearly. Instead of storing one number, each replica stores **one number per region**: how many increments that region has made. A region only ever increments its own entry. To merge another replica's state, take the **maximum** of each entry. The value is the sum of the entries.

```text
us-east: {us: 5, eu: 0}   +   eu-west: {us: 0, eu: 3}   →   merged: {us: 5, eu: 3} = 8
```

Taking the maximum makes merging **commutative** (order doesn't matter), **associative** (grouping doesn't matter), and **idempotent** (merging the same state twice changes nothing). That's exactly what you need over an unreliable network that delays, reorders, and duplicates messages. Increments are never lost, because each region's entry only grows. To support decrements, keep a second map of decrements, a **PN-counter** (positive-negative). The same idea, a state that only grows under a merge, gives sets, registers, maps, and even collaborative text editing.

Next, a short check on what you just read.
