# Read-Your-Writes and Monotonic Reads

*Chapter 5 · Replication and Caching.*

## Read-your-writes

A user edits their profile, saves, and the page reloads. The write went to the leader, but the reload read from a follower that hasn't applied it yet. The edit seems to have vanished. The user tries again, creating a duplicate, or files a bug report.

**Read-your-writes** (also called **read-after-write consistency**) guarantees that a user always sees their *own* updates. It promises nothing about other users' updates, which may still appear late. Ways to provide it:

- **Read things the user may have modified from the leader.** A user's own profile is only edited by that user, so read it from the leader and other people's profiles from followers. It's simple, but it only works when you can tell in advance what a user may have changed.
- **Read from the leader for a while after any write**, say one minute, or as long as followers usually lag. You can also stop reading from followers whose measured lag exceeds the window.
- **Track the write's position.** The client remembers the LSN (or a timestamp) of its latest write. A read goes to a follower only if that follower has applied at least that position. Otherwise, the read waits for the follower to catch up, goes to another follower, or falls back to the leader. This is the most precise approach, because it waits for exactly the write that matters. Databases support it directly: MySQL's `WAIT_FOR_EXECUTED_GTID_SET()` waits until a replica has applied given transactions, and MongoDB's **causally consistent sessions** attach an `afterClusterTime` to each read so a secondary waits until it has caught up to that point.

Complications appear quickly:

- **Cross-device**: a user writes on their phone and reads on their laptop. The laptop doesn't know the phone's LSN, so the position must be stored centrally, per user, not per device.
- **Multiple data centers**: requests from the same user may be routed to different regions, and the leader for their data may be far away. You may need to route all of a user's requests to one region.
- **Caches**: a cache in front of the followers (covered later in this chapter) must respect the same rule, or it simply replays the stale value for its whole TTL.

## Monotonic reads

A user loads a comment thread and sees a new comment. They refresh, and it's gone. They refresh again, and it's back. Each read went to a different follower, and the second follower lagged further behind than the first. To the user, **time moved backward**.

**Monotonic reads** guarantees that once a user has seen data as of some point, later reads never show an *older* state. It's weaker than strong consistency (the data can still be stale) but stronger than eventual consistency (it never goes backward). Ways to provide it:

- **Sticky routing**: send each user's reads to the same follower, for example by hashing the user id to choose one. That follower's state only moves forward. If it fails, the user must be rerouted, and the guarantee needs the next approach to survive the switch.
- **Track the highest position read**: like read-your-writes, but the session remembers the newest state it has *read*, not just written, and never reads from a follower that's behind it. This works with any number of followers, including after failover.

The two guarantees combine naturally: the session's minimum acceptable position is the larger of the latest write it made and the newest state it read.

Next, a short check on what you just read.
