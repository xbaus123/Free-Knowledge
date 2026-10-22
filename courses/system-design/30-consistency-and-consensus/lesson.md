# Consistency and Consensus

*Based on* Designing Data-Intensive Applications*, Chapter 9.*

The last lessons were about everything that goes wrong: lost messages, lying clocks, paused processes. The best way to build fault-tolerant systems is to find general-purpose **abstractions** with useful guarantees, implement them once, and let applications rely on them. The most important is **consensus**: getting several nodes to agree on something, despite failures.

## Linearizability

Most replicated databases offer **eventual consistency**: stop writing, wait, and the replicas converge. Until then, different replicas give different answers.

**Linearizability** (also called *strong consistency* or *atomic consistency*) is the strongest guarantee: the system behaves as if there were **a single copy of the data**, and every operation takes effect atomically at some instant between its start and its end. Once any read has returned a new value, every later read, by anyone, must return that value or a newer one.

Example: Alice refreshes a sports score page and sees "Final score: 2–1". She tells Bob, who refreshes and still sees "Match in progress", because his request hit a lagging replica. That's a linearizability violation: Bob's read started after Alice's finished, yet saw older data.

Where you need it:

- **Locks and leader election**: everyone must agree who holds the lock.
- **Uniqueness constraints**: two users can't claim the same username or the same seat.
- **Cross-channel timing**: a web server writes a photo to storage and sends a resize job over a queue. The resizer must see the photo.

What provides it: single-leader replication *can*, if reads go to the leader. Consensus algorithms do. Multi-leader and leaderless (Dynamo-style) replication generally don't, and neither does last write wins.

### The cost: the CAP theorem, stated properly

When a **network partition** separates replicas, you must choose:

- Stay **consistent** (linearizable): the side that can't reach a quorum must refuse requests, so it's unavailable.
- Stay **available**: both sides keep answering, so they can diverge.

That's CAP: *when partitioned*, choose consistency or availability. It's not "pick two of three", since partitions aren't optional. Linearizability is also slow even without partitions: every operation waits on coordination, so many systems give it up for **performance**, not just fault tolerance.

## Ordering and causality

Much of consistency is about **order**. **Causality** says that if a question comes before its answer, everyone should see them in that order. Causal consistency is weaker than linearizability, and much cheaper.

**Lamport timestamps** order events with logical clocks:

- Each node keeps a counter and attaches `(counter, node id)` to every operation.
- Every node also tracks the highest counter it has seen in any message, and jumps its own counter past it.
- The result is a **total order** consistent with causality.

But a total order discovered *after the fact* isn't enough to enforce a uniqueness constraint *right now*. A node claiming a username can't know whether some other node is about to claim it with a lower timestamp. You need to know the order is final.

## Total order broadcast

**Total order broadcast** (also called atomic broadcast) delivers messages to all nodes:

- **Reliably**: if a message reaches one node, it reaches all of them.
- **In the same order everywhere.**

It's exactly what **state machine replication** needs. Feed every replica the same writes in the same order, and they all end up in the same state. It's equivalent to consensus, and it's how ZooKeeper and etcd work: their **log** is a totally ordered broadcast. You can build a linearizable compare-and-set on it: append "claim username alice", then read the log; the first claim in the log wins.

## Distributed transactions: two-phase commit

How do you commit a transaction atomically across several nodes, so that all commit or all abort? **Two-phase commit (2PC)** uses a **coordinator**:

1. **Prepare**: the coordinator asks every participant, "Can you commit?" Each one makes sure it can (writing everything to disk), then votes **yes**. A yes is a *promise*: the participant can no longer abort on its own.
2. **Commit**: if *all* voted yes, the coordinator writes its decision to its own log (the **commit point**), then tells everyone to commit. If anyone voted no, everyone aborts.

The weakness: if the coordinator crashes after participants voted yes, they're **in doubt**. They can't commit or abort until it recovers, and they hold their locks the whole time. 2PC is a **blocking** protocol, and the coordinator is a single point of failure. XA transactions across different technologies are notoriously painful to operate for this reason. Microservices usually avoid 2PC altogether and use **sagas** instead (lesson 32).

## Consensus

Formally, consensus means several nodes propose values and decide on one, such that:

- **Uniform agreement**: no two nodes decide differently.
- **Integrity**: no node decides twice.
- **Validity**: the decided value was proposed by some node.
- **Termination**: every node that doesn't crash eventually decides, as long as a **majority** is working.

Termination is what 2PC lacks. Well-known algorithms: Paxos, Zab (ZooKeeper), Viewstamped Replication, and **Raft**.

## Raft

Raft was designed to be understandable. It decomposes consensus into three parts.

### 1. Leader election

- Time is divided into numbered **terms**, and each term has at most one leader.
- Followers expect regular **heartbeats** from the leader. If a follower's randomized **election timeout** runs out, it becomes a **candidate**: it increments the term, votes for itself, and asks the others for votes.
- Each node votes at most once per term. A candidate with a **majority** becomes leader.
- Any node that sees a higher term steps down to follower.

Two majorities always overlap, and each node votes once per term, so **two leaders can never be elected in the same term**. Randomized timeouts make split votes rare.

### 2. Log replication

- Clients send commands to the leader, which appends them to its log and replicates them to followers with `AppendEntries`.
- Once a **majority** has stored an entry, it's **committed**, and every node applies committed entries to its state machine, in log order.
- `AppendEntries` includes the previous entry's index and term, and a follower rejects it if its log doesn't match. On rejection, the leader backs up and retries until the logs agree. Logs are always consistent.

### 3. Safety

A node only votes for a candidate whose log is **at least as up to date** as its own. So any newly elected leader already has every committed entry, and committed entries are never lost.

### Raft in practice

etcd (which stores Kubernetes' state), Consul, CockroachDB, TiKV, and Kafka's KRaft mode all run Raft.

Consensus needs a strict majority, so a 3-node cluster tolerates 1 failure and a 5-node cluster tolerates 2. Every decision waits on a majority round trip, so you usually don't run consensus over all your data. Instead, a small consensus service (ZooKeeper, etcd) handles:

- Leader election for other systems.
- Distributed locks with **fencing tokens**: the zxid or revision number serves as the token.
- Membership and service discovery.
- Configuration and partition assignment.

In the next lesson, you'll implement Raft's leader election and heartbeats, and the grader will kill your leader.

## Key terms

| Term | Meaning |
|---|---|
| Linearizability | Behaves like a single copy; reads never go back in time |
| CAP | During a partition, choose consistency or availability |
| Causality | If A caused B, everyone sees A before B |
| Lamport timestamp | A logical clock giving a causality-consistent total order |
| Total order broadcast | All nodes deliver the same messages in the same order |
| Two-phase commit | Prepare, then commit, under a coordinator; blocks if the coordinator dies |
| Consensus | Nodes agree on a value despite failures, given a majority |
| Term | Raft's election epoch; at most one leader per term |
