# Capstone: Design a Twitter Timeline

Time to put everything together. You're designing the home timeline service of a Twitter-like product, starting from an **empty canvas**.

## Load parameters

| | Real system | In the simulator (1:500) |
|---|---|---|
| Timeline reads | 1,000,000 / s | ~2,000 / s |
| New tweets | 20,000 / s | ~40 / s |
| Fan-out | Each tweet is copied into its followers' home timelines | Each tweet costs the database **100 writes** (400 ms of work) |

Reads favor popular timelines. Users expect reads in well under **200 ms (p99)**, and a posted tweet to be acknowledged within **100 ms**. The fan-out can happen in the background, but tweets should start reaching timelines within **half a second**.

## What the simulator throws at you

The run lasts two seconds:

| Time | Event |
|---|---|
| 400 ms | **A bot floods the API at 100× normal traffic** for 100 ms |
| 700 ms | **An API server's host dies** |
| 1,000 ms | **The timelines database's primary crashes** |
| 1,300 ms | **A tweet goes viral**: extra reads of one timeline add 50% to traffic for 300 ms |
| 1,500 ms | **A network partition** cuts the load balancer off from an API server for 200 ms |

## Goals

- **p99 latency ≤ 200 ms** for real users (bot traffic doesn't count)
- **Write acknowledgment ≤ 100 ms** (p99)
- **Queue wait ≤ 500 ms** before a consumer picks up a tweet
- **At most 5% of requests fail** (some loss during crashes is unavoidable; the bot's requests don't count)
- No overloaded components, and every queued write reaches the database
- **Budget: $400/month**

## Your components

| Component | Cost | Capacity and behavior |
|---|---|---|
| Rate Limiter | $10 | Token bucket per user (default 20 req/s). Real users send about 2/s each. |
| CDN | $15 | Serves static files (there are none here: every request is dynamic) |
| Load Balancer | $20 | Health checks notice dead servers after ~100 ms |
| Server | $10 | 4 connections × 6 ms ≈ 667 req/s; +$10 per extra connection |
| Cache | $25 | 20 connections × 0.5 ms; loads misses from a replica, or else the database |
| Database | $50 per partition | 10 connections × 4 ms per partition. A standby (sync or async) fails over in 150 ms, for +$40 per partition. |
| Read Replica | $40 | 10 connections × 4 ms; draw an edge from the database to it |
| Message Queue | $20 | Acknowledges writes immediately; delivers to its subscribers with N **consumers** in parallel (default 4, up to 32), retrying failures |

Remember the routing rules: servers send reads to a cache first, then a replica, then the database. Writes go to a queue first, then a cache, then the database.

You've studied each piece in depth: load balancers in lesson 8, caching in lesson 21, and queues in lesson 33. The results panel and the replay timeline are your observability (lesson 36): read them the way you'd read a dashboard and a trace.

## How to approach it

Do the back-of-the-envelope math from lesson 6 before you draw anything. Then build in layers, simulating after each:

1. **Serve the reads.** How many servers do ~2,000 req/s need, with headroom for a dead server and a viral spike?
2. **Protect the database.** Every read that reaches the database competes with 400-ms fan-out writes for its connections. Where should reads go instead?
3. **Absorb the writes.** A tweet that waits for its fan-out can't be acknowledged in 100 ms. How many consumers keep up with 40 tweets/s at 400 ms each, and how many database partitions do they need?
4. **Survive the faults.** Replay the run and check each fault in the event list. What stops the bot? What takes over when the primary dies? What keeps working when a server disappears?

There's more than one passing design. When yours passes, open the **⚡ Chaos** toolkit and find out **what breaks first** when you take away one more piece.

> **Think about it.** Real Twitter fans tweets out on write for most users, but celebrities with millions of followers are merged in at read time instead. Where would that change your design, and what would it cost on the read path?
