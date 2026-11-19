# Two-Phase Commit and Consensus

*Chapter 8 · Consistency and Consensus.*

## Distributed transactions: two-phase commit

How do you commit a transaction atomically across several nodes, so that all commit or all abort? **Two-phase commit (2PC)** uses a **coordinator**:

1. **Prepare**: the coordinator asks every participant, "Can you commit?" Each one makes sure it can (writing everything to disk), then votes **yes**. A yes is a *promise*: the participant can no longer abort on its own.
2. **Commit**: if *all* voted yes, the coordinator writes its decision to its own log (the **commit point**), then tells everyone to commit. If anyone voted no, everyone aborts.

The weakness: if the coordinator crashes after participants voted yes, they're **in doubt**. They can't commit or abort until it recovers, and they hold their locks the whole time. 2PC is a **blocking** protocol, and the coordinator is a single point of failure. XA transactions across different technologies are notoriously painful to operate for this reason. Microservices usually avoid 2PC altogether and use **sagas** instead (chapter 9).

## Consensus

Formally, consensus means several nodes propose values and decide on one, such that:

- **Uniform agreement**: no two nodes decide differently.
- **Integrity**: no node decides twice.
- **Validity**: the decided value was proposed by some node.
- **Termination**: every node that doesn't crash eventually decides, as long as a **majority** is working.

Termination is what 2PC lacks. Well-known algorithms: Paxos, Zab (ZooKeeper), Viewstamped Replication, and **Raft**.

Next, a short check on what you just read.
