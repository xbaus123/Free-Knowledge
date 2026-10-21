# Replication and Caching: Fresh Reads at Scale

Your photo-sharing site is popular, and the architecture shows the strain. Load for this run:

- **3,500 requests in one second**: 55% reads of posts, 35% static files (images, scripts), 10% writes.
- Everyone who posts **reloads 30 ms later** to see their post. Users expect **read-your-writes**.

Someone already added a **read replica** to take reads off the Postgres primary. Each API server writes to the primary and reads from the replica. Click **Simulate Traffic** to see how that's going.

## Two problems

**1. Users see stale data.** The replica receives changes asynchronously and trails the primary by **50 ms**. A user who reloads 30 ms after posting reads from a replica that hasn't seen the post yet. That's the replication lag anomaly from the last lesson.

**2. The servers are drowning in static files.** Over a third of the requests are for images and scripts that never change, yet every one passes through an API server.

## Your tools

| Component | Cost | What it does |
|---|---|---|
| **CDN** | $15 | Put it between the Client and the load balancer. It serves static files from the edge after the first request and passes everything else on. |
| **Cache** (Redis) | $25 | Servers send reads to a connected cache first. It answers what it holds and loads misses from the store behind it (a replica, or else the database). Writes pass through it to the database. |
| Read Replica | $40 | A lagging copy of the primary. Servers prefer it for reads. |
| Database | $50 | 10 connections × 4 ms ≈ 2,500 queries/s |
| Server | $10 | 4 connections × 6 ms ≈ 667 requests/s |

**Double-click the cache** to choose what happens when data changes:

- **Expire after a TTL**: writes pass through untouched, and cached copies stay until they expire. Readers see old data in the meantime.
- **Invalidate on write**: a write through the cache deletes the cached copy, so the next read loads the new value.

## Your task

Meet all three goals on a budget of **$160/month**:

- **p99 latency ≤ 150 ms**
- **Stale reads ≤ 1%**
- No overloaded components

The results panel shows the stale-read rate, the cache hit rate, and how much the CDN served. Replay the run and watch where the load goes.

Some hints, if you want them:

- Sending every read straight to the primary fixes staleness, but count its load: about 2,300 reads plus 350 writes a second.
- Ask yourself where the cache should **load misses from**, and whether the replica still earns its $40 once the cache is in place.

> **Think about it.** Invalidate-on-write keeps the cache fresh, but there's still a race. A read misses, loads the old value from the database, and a write invalidates the key *before* that read stores its stale copy. How do real systems narrow that window? (Look up "cache stampede" and "lease"-based caching, as in Facebook's memcache paper.)
