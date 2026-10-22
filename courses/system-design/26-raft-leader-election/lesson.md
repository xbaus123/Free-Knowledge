# Raft: Leader Election and Heartbeats

Consensus starts with agreeing on **who's in charge**. In Raft, one node is the **leader**. It handles all requests and tells the others what to do. If it dies, the rest must notice and elect a replacement quickly, and must never end up with two leaders that both believe they're in charge.

You'll write the election half of Raft: terms, voting, and heartbeats. (The full algorithm also replicates a log; that's beyond this lesson, so votes don't compare logs here.)

## The rules

Every node is a **follower**, a **candidate**, or the **leader**. Time is divided into numbered **terms**, and each term has at most one leader.

1. **Followers wait.** Each follower has an **election timer** set to a random 150–300 ms. Hearing from the leader resets it. If it runs out, the follower assumes the leader is dead.
2. **Candidates campaign.** A node whose timer runs out:
   - Increments its term and becomes a **candidate**.
   - Votes for itself.
   - Resets its timer, in case this election splits the vote.
   - Sends `RequestVote(term, candidate)` to every peer.
3. **Voters vote once per term.** A node grants its vote only if the request is for its current term and it hasn't already voted for someone else in that term. It replies with `Vote(term, voter, granted)`, and resets its timer when it grants a vote.
4. **A majority wins.** A candidate with votes from a majority of the cluster (2 of 3, or 3 of 5), counting its own, becomes **leader**.
5. **Leaders send heartbeats.** The leader sends `Heartbeat(term, leader)` to everyone every 50 ms, starting immediately. A node hearing a heartbeat for its current term becomes (or stays) a follower and resets its timer. It always replies with `HeartbeatReply(term, follower)`.
6. **Newer terms win.** Any message with a **higher** term than yours means you're out of date. Adopt that term and become a follower before handling the message. This is how a crashed leader that comes back learns it's been replaced.

Why does this work? A candidate needs a majority, each node votes once per term, and two majorities always share a node, so **two leaders can't win the same term**. Randomized timeouts make it likely that one node times out first and wins before the others even start, so split votes are rare and short.

## The files

- **`messages.py`** (read-only): `RequestVote`, `Vote`, `Heartbeat`, `HeartbeatReply`.
- **`cluster.py`** (read-only): a simulated network. Each node gets an `env`:
  - `env.now`: simulated milliseconds since start.
  - `env.random`: the node's own random number generator.
  - `env.send(peer, msg)`: sends a message, delivered 2–10 ms later, or lost if the peer is down or partitioned away.

  The cluster calls each node's `tick()` every 5 ms and `on_message(msg)` for each delivery.
- **`raft.py`**: yours. `__init__`, `reset_election_timer()`, `become_follower(term)`, `majority()`, and `broadcast(msg)` are provided. Fill in `tick`, `start_election`, `become_leader`, and `on_message`.

## How it's graded

The grader runs **three copies of your class** (five in some tests) in the simulated network:

- One leader is elected within a second, and it stays leader for 5 seconds when nothing fails.
- No node ever votes twice in a term, and **no term ever has two leaders**, even with 15–20% of messages dropped and leaders crashing and coming back.
- The grader **kills the leader at a random moment**. A new leader must be elected **within 1,000 ms**, in a higher term.
- When the old leader comes back, it must step down.
- In a network partition, only the side with a majority can elect a leader.

Each test runs several random seeds. Simulated time makes every run reproducible: the same seed always replays the same messages in the same order. Real Raft implementations, like etcd's, are tested the same way, because bugs that need one specific interleaving of messages are otherwise nearly impossible to reproduce.

Try it in the **Scratchpad**:

```python
from cluster import Cluster
from raft import RaftNode

c = Cluster(RaftNode, n=3, seed=1)
c.run(1000)
print(c.leaders(), {nid: (n.role, n.term) for nid, n in c.nodes.items()})
```

## Think about it

- Why must the election timeout be much longer than the heartbeat interval, and much longer than a message's round trip?
- With 5 nodes, how many can fail before the cluster stops electing leaders?
- A node cut off in a minority keeps timing out and incrementing its term. When the partition heals, its high term forces the healthy leader to step down. Raft's **PreVote** extension fixes this disruption. How might it work?
