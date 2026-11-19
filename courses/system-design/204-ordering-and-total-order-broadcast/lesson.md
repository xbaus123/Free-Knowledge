# Ordering, Causality, and Total Order Broadcast

*Chapter 8 · Consistency and Consensus.*

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

Next, a short check on what you just read.
