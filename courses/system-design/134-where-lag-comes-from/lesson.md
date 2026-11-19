# Where Replication Lag Comes From

*Chapter 5 · Replication and Caching.*

*Based on* Designing Data-Intensive Applications*, Chapter 5.*

An earlier reading listed three anomalies that asynchronous followers cause, in one table. The next readings take them apart. Replication lag isn't a bug you can fix once. It's a permanent property of any system that serves reads from copies, and the question is which promises you make to users anyway. You'll measure lag, and then build the three guarantees that tame it: **read-your-writes**, **monotonic reads**, and **consistent prefix reads**.

## Where lag comes from

With asynchronous single-leader replication, the leader commits a write, answers the client, and *then* ships the change to its followers through the replication log. Each follower applies the log in order, some time later. That delay is the **replication lag**.

On a healthy system in one data center, lag is usually a few milliseconds. But nothing bounds it:

- **Load**: a follower busy serving reads applies the log more slowly. A burst of writes, like a migration that rewrites a big table, can leave every follower minutes behind.
- **Long transactions and big rows**: a follower applies changes in commit order, so one huge transaction holds up everything behind it.
- **Network trouble**: a congested or flapping link between regions (chapter 6) stretches lag to seconds or minutes.
- **Recovery**: a follower that restarts, or is newly added, may be hours behind while it catches up.
- **Single-threaded apply**: some databases replay the log on one thread, so a leader that writes with 32 cores in parallel can outrun a follower applying on one.

If you stop writing, every follower eventually catches up and holds the same data. That's **eventual consistency**, and "eventually" carries no promise about when. An application that reads from followers must assume any read can be stale by an arbitrary amount, unless it does something about it.

## Measuring lag

You can only manage what you measure. There are two natural units, and you want both:

- **Writes behind**: the leader's log position minus the follower's. Databases expose positions as **log sequence numbers (LSNs)** in PostgreSQL, **GTIDs** (global transaction ids) in MySQL, and **oplog timestamps** in MongoDB. A difference of 0 means caught up.
- **Seconds behind**: how long ago the oldest change the follower *hasn't* applied was committed. That's what users feel: how stale is the data I'm reading?

They diverge in revealing ways. A leader writing 50,000 changes a second can be 50,000 writes behind yet only one second stale. A quiet leader can be one write behind for a whole minute, because the change that would show up as a large gap simply hasn't happened yet. Naive "seconds behind" metrics compare the timestamp of the last applied change with the current time, which makes an idle but fully caught-up follower look stale. Many teams instead have the leader write a **heartbeat** row with the current time every second, and measure lag as the age of the newest heartbeat a follower has applied.

Alert on lag as you would on latency (chapter 10), and **take a follower out of the read pool** when it falls too far behind. A load balancer that checks only whether a follower is *up* will happily route reads to one that's an hour stale.

Next, a short check on what you just read.
