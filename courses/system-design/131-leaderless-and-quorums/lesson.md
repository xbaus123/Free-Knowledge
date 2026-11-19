# Leaderless Replication and Quorums

*Chapter 5 · Replication and Caching.*

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

Next, a short check on what you just read.
