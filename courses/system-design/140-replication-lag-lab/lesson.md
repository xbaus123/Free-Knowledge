# Replication Lag: Read-Your-Writes, Monotonic Reads, and Consistent Prefixes

*Chapter 5 · Replication and Caching.*

Build the guarantees from the last three readings: measure lag, then enforce read-your-writes, monotonic reads, and consistent prefix reads.

## Your task

`solution.py` provides a simulated cluster: a `Clock` you advance, a `Leader` whose `write(key, value)` returns the write's LSN (1 for the first write), and `Follower`s that apply the leader's log `lag` seconds after each write. `follower.applied_lsn` is how many log entries a follower has applied, and `read(key)` on either returns `(value, lsn)`, the LSN being the state the read saw. Both count their `reads`. `leader.log[i]` is `(commit time, key, value)` for LSN `i + 1`.

### 1. Measuring lag

`lag_report(leader, followers)` returns `{follower name: (writes behind, seconds behind)}`. Writes behind is the leader's LSN minus the follower's `applied_lsn`. Seconds behind is how long ago the first write the follower hasn't applied was committed, or `0.0` if it's caught up.

### 2. Session guarantees

`Session(leader, followers, read_your_writes=False, monotonic_reads=False)` is one user's view of the cluster.

- `write(key, value)` writes to the leader and records the LSN in `self.write_lsn`.
- `read(key)` returns the value, reading from a **follower** whenever one is good enough:
  - Work out the minimum LSN the read needs: `self.write_lsn` with read-your-writes, `self.read_lsn` with monotonic reads, the larger of the two with both, and 0 with neither.
  - Try the followers in rotation: the first read starts with follower 0, the next with follower 1, and so on (`self.turn`), wrapping around. Read from the first one whose `applied_lsn` is at least the minimum. If none is, read from the leader.
  - Update `self.read_lsn` to the LSN the read returned, if it's newer.

A test runs a random workload and checks that a session with both guarantees never sees a key go back in time, while most of its reads still go to followers.

### 3. Consistent prefix reads

`CausalReader` receives writes from several partitions' replication streams in whatever order they arrive. Each write is a dict with an `id` and `deps`, the ids of the writes it depends on.

- `receive(write)` makes the write **visible** (appends its id to `self.visible`) once every one of its dependencies is visible. Until then, it waits. Making one write visible may release others that were waiting for it, and those may release more. Release waiting writes in the order they arrived.
- A write delivered twice is ignored the second time.
- `pending()` lists the ids of writes still waiting, in arrival order.

See the anomalies yourself in the **Scratchpad**:

```python
from solution import Clock, Follower, Leader

clock = Clock()
leader = Leader(clock)
fast, slow = Follower("fast", leader, 0.01), Follower("slow", leader, 1.0)
leader.write("comment", "first!")
clock.advance(0.5)
print(fast.read("comment"), slow.read("comment"))  # refresh, and it's gone
```

## Think about it

- Your session stores its positions in memory. Where would you keep them for a web app whose users have several devices, and what happens when that store is unavailable?
- A follower is taken out of the read pool when it's more than 10 seconds behind. All followers fall behind at once during a big migration. What happens to the leader, and what would you do instead?
- With one leader, your sessions get monotonic writes for free. Which of the four session guarantees would break first if any region could accept writes (chapter 6), and what would the session have to track?

## Key terms

| Term | Meaning |
|---|---|
| Replication lag | How far a follower trails its leader, in writes or in seconds |
| Eventual consistency | Replicas converge once writes stop, with no bound on when |
| LSN | Log sequence number: a position in the replication log |
| Heartbeat table | A row the leader updates on a timer, to measure lag in seconds |
| Read-your-writes | A user always sees their own earlier writes |
| Monotonic reads | A user never sees an older state after a newer one |
| Consistent prefix reads | Writes are seen in the order they happened, without gaps |
| Session guarantees | Promises about one client's view: read your writes, monotonic reads, writes follow reads, monotonic writes |
| Causal consistency | Everyone sees causes before their effects |
| Bounded staleness | Reads are at most a fixed time or number of versions behind |
