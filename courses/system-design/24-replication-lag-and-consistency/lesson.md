# Replication Lag: Read-Your-Writes, Monotonic Reads, and Consistent Prefixes

*Based on* Designing Data-Intensive Applications*, Chapter 5.*

The last lesson listed three anomalies that asynchronous followers cause, in one table. This lesson takes them apart. Replication lag isn't a bug you can fix once. It's a permanent property of any system that serves reads from copies, and the question is which promises you make to users anyway. You'll measure lag, and then build the three guarantees that tame it: **read-your-writes**, **monotonic reads**, and **consistent prefix reads**.

## Where lag comes from

With asynchronous single-leader replication, the leader commits a write, answers the client, and *then* ships the change to its followers through the replication log. Each follower applies the log in order, some time later. That delay is the **replication lag**.

On a healthy system in one data center, lag is usually a few milliseconds. But nothing bounds it:

- **Load**: a follower busy serving reads applies the log more slowly. A burst of writes, like a migration that rewrites a big table, can leave every follower minutes behind.
- **Long transactions and big rows**: a follower applies changes in commit order, so one huge transaction holds up everything behind it.
- **Network trouble**: a congested or flapping link between regions (lesson 28) stretches lag to seconds or minutes.
- **Recovery**: a follower that restarts, or is newly added, may be hours behind while it catches up.
- **Single-threaded apply**: some databases replay the log on one thread, so a leader that writes with 32 cores in parallel can outrun a follower applying on one.

If you stop writing, every follower eventually catches up and holds the same data. That's **eventual consistency**, and "eventually" carries no promise about when. An application that reads from followers must assume any read can be stale by an arbitrary amount, unless it does something about it.

## Measuring lag

You can only manage what you measure. There are two natural units, and you want both:

- **Writes behind**: the leader's log position minus the follower's. Databases expose positions as **log sequence numbers (LSNs)** in PostgreSQL, **GTIDs** (global transaction ids) in MySQL, and **oplog timestamps** in MongoDB. A difference of 0 means caught up.
- **Seconds behind**: how long ago the oldest change the follower *hasn't* applied was committed. That's what users feel: how stale is the data I'm reading?

They diverge in revealing ways. A leader writing 50,000 changes a second can be 50,000 writes behind yet only one second stale. A quiet leader can be one write behind for a whole minute, because the change that would show up as a large gap simply hasn't happened yet. Naive "seconds behind" metrics compare the timestamp of the last applied change with the current time, which makes an idle but fully caught-up follower look stale. Many teams instead have the leader write a **heartbeat** row with the current time every second, and measure lag as the age of the newest heartbeat a follower has applied.

Alert on lag as you would on latency (lesson 40), and **take a follower out of the read pool** when it falls too far behind. A load balancer that checks only whether a follower is *up* will happily route reads to one that's an hour stale.

## Read-your-writes

A user edits their profile, saves, and the page reloads. The write went to the leader, but the reload read from a follower that hasn't applied it yet. The edit seems to have vanished. The user tries again, creating a duplicate, or files a bug report.

**Read-your-writes** (also called **read-after-write consistency**) guarantees that a user always sees their *own* updates. It promises nothing about other users' updates, which may still appear late. Ways to provide it:

- **Read things the user may have modified from the leader.** A user's own profile is only edited by that user, so read it from the leader and other people's profiles from followers. It's simple, but it only works when you can tell in advance what a user may have changed.
- **Read from the leader for a while after any write**, say one minute, or as long as followers usually lag. You can also stop reading from followers whose measured lag exceeds the window.
- **Track the write's position.** The client remembers the LSN (or a timestamp) of its latest write. A read goes to a follower only if that follower has applied at least that position. Otherwise, the read waits for the follower to catch up, goes to another follower, or falls back to the leader. This is the most precise approach, because it waits for exactly the write that matters. Databases support it directly: MySQL's `WAIT_FOR_EXECUTED_GTID_SET()` waits until a replica has applied given transactions, and MongoDB's **causally consistent sessions** attach an `afterClusterTime` to each read so a secondary waits until it has caught up to that point.

Complications appear quickly:

- **Cross-device**: a user writes on their phone and reads on their laptop. The laptop doesn't know the phone's LSN, so the position must be stored centrally, per user, not per device.
- **Multiple data centers**: requests from the same user may be routed to different regions, and the leader for their data may be far away. You may need to route all of a user's requests to one region.
- **Caches**: a cache in front of the followers (lesson 25) must respect the same rule, or it simply replays the stale value for its whole TTL.

## Monotonic reads

A user loads a comment thread and sees a new comment. They refresh, and it's gone. They refresh again, and it's back. Each read went to a different follower, and the second follower lagged further behind than the first. To the user, **time moved backward**.

**Monotonic reads** guarantees that once a user has seen data as of some point, later reads never show an *older* state. It's weaker than strong consistency (the data can still be stale) but stronger than eventual consistency (it never goes backward). Ways to provide it:

- **Sticky routing**: send each user's reads to the same follower, for example by hashing the user id to choose one. That follower's state only moves forward. If it fails, the user must be rerouted, and the guarantee needs the next approach to survive the switch.
- **Track the highest position read**: like read-your-writes, but the session remembers the newest state it has *read*, not just written, and never reads from a follower that's behind it. This works with any number of followers, including after failover.

The two guarantees combine naturally: the session's minimum acceptable position is the larger of the latest write it made and the newest state it read.

## Consistent prefix reads

The third anomaly is subtler. In a partitioned database (lesson 26), each partition has its own leader and replicates independently. Suppose a question is posted to one partition, and the answer, written afterward, goes to another. If an observer reads from followers, and the answer's partition happens to replicate faster, the observer sees the **answer before the question**: an effect without its cause.

```text
partition 1:  "Does anyone know when the store closes?"  ─── replicates slowly ───▶  observer sees it second
partition 2:  "At 9 tonight."                            ─ replicates quickly ─▶     observer sees it first
```

**Consistent prefix reads** guarantees that if a sequence of writes happens in some order, anyone reading them sees them in that order, without gaps: some *prefix* of the true history, never the history with pieces missing from the middle. Within a single partition with single-leader replication, that's free: the log is applied in order. Across partitions, there's no global order.

Solutions:

- **Keep causally related writes in one partition.** Put a conversation's messages in the partition of the conversation, not of the author. Often the best answer, though not always possible.
- **Track causal dependencies.** Each write records which earlier writes it depends on: the reply depends on the question. A reader holds back a write until everything it depends on is visible. This is **causal consistency**, the strongest consistency model that doesn't require coordination and stays available during network partitions. Tracking dependencies precisely takes metadata, and systems use **version vectors** or **hybrid logical clocks** to summarize it compactly.
- **Use a total order.** A consensus-based log (lesson 34) or a timestamp oracle orders every write in the database, at the cost of a coordination round trip.

## Session guarantees, formally

These guarantees come from research on the Bayou system at Xerox PARC in 1994, which defined four **session guarantees** for clients of eventually consistent replicas:

| Guarantee | Promise to a session | The anomaly it prevents |
|---|---|---|
| **Read your writes** | Reads reflect the session's own earlier writes | My edit disappeared |
| **Monotonic reads** | Reads never return an older state than an earlier read | The comment appeared, then vanished |
| **Writes follow reads** | A write is ordered after any write the session read before it | My reply was applied before the post I replied to |
| **Monotonic writes** | The session's writes are applied in the order it made them | My "delete" was applied before my "create" |

All four are about a *session*: one user's view, not the whole system's. That's what makes them cheap. They need only per-session metadata, like the positions you'll track, rather than coordination between replicas. Together, they add up to causal consistency for that session.

How they relate to the stronger models:

| Model | What every reader sees | Cost |
|---|---|---|
| **Eventual consistency** | Something, eventually the same thing | Nothing extra |
| **Session guarantees** | A view consistent with its own history | Per-session positions; sometimes a leader read or a wait |
| **Causal consistency** | Causes before effects, for everyone | Dependency tracking |
| **Bounded staleness** | Data at most *t* seconds or *k* versions old | Lag monitoring and routing (Azure Cosmos DB offers it directly) |
| **Linearizability** | The latest write, as if there were one copy | Coordination on every read (lessons 34 and 35) |

Choosing between them is a product decision as much as an engineering one. A like count that's two seconds stale harms nobody. A bank balance that goes backward will generate support calls. Many applications use read-your-writes and monotonic reads for user-facing pages, causal ordering for conversations, and linearizable reads only for the few operations that need them, like checking a username is free or a seat is still available.

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
- With one leader, your sessions get monotonic writes for free. Which of the four session guarantees would break first if any region could accept writes (lesson 28), and what would the session have to track?

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
