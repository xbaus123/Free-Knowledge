# Linearizability and CAP

*Chapter 8 · Consistency and Consensus.*

*Based on* Designing Data-Intensive Applications*, Chapter 9.*

*Based on* Designing Data-Intensive Applications*, Chapter 9.*

The last chapter was about everything that goes wrong: lost messages, lying clocks, paused processes. The best way to build fault-tolerant systems is to find general-purpose **abstractions** with useful guarantees, implement them once, and let applications rely on them. The most important is **consensus**: getting several nodes to agree on something, despite failures.

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

Next, a short check on what you just read.
