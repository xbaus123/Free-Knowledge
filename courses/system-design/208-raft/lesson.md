# Raft

*Chapter 8 · Consistency and Consensus.*

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

Right after this reading's check, you'll implement Raft's leader election and heartbeats, and the grader will kill your leader.

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

Next, a short check on what you just read.
