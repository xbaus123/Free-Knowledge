# How Small Faults Become Outages

*Chapter 7 · Transactions and Fault Tolerance.*

*Based on* Designing Data-Intensive Applications*, Chapters 1 and 8.*

*Based on* Designing Data-Intensive Applications*, Chapters 1 and 8.*

The distributed trouble lesson was the diagnosis. Networks lose and delay messages without bound, processes pause, clocks drift, and a timeout can't tell a dead node from a slow one. The next readings are the treatment: the patterns that keep a system working while the things it depends on are failing.

Chapter 1 drew the line between a **fault** (one component deviating from its spec) and a **failure** (the system as a whole stops serving users). You can't prevent faults. These patterns stop them from turning into failures, and above all from **spreading**.

## How small faults become outages

Most large outages don't start large. They start with one slow dependency, and the system's own reactions make it worse.

**Cascading failure.** A recommendations service slows from 20 ms to 2 seconds, perhaps because of a garbage collection storm. The product page calls it synchronously with no timeout. The page servers have 200 worker threads each. Each request now holds a thread for 2 seconds instead of 50 ms, so the servers handle 100 requests a second instead of 4,000. Their queues fill, their own latency soars, and the gateway's calls to them time out. A slow, *non-essential* feature has taken down the product page, and anything else that shared those threads.

**Retry storms.** Clients that time out retry. Each retry is another request to an already overloaded service. If each of four layers retries 3 times, one failing call at the bottom becomes 3⁴ = 81 attempts, and the struggling service sees its load multiply exactly when it can least afford it.

**Metastable failure.** Sometimes the system stays down even after the trigger is gone. A brief database blip empties a cache, and the cold cache sends ten times the usual load to the database. Timeouts and retries keep that load above what the database can serve, so the cache never warms back up. The system is stable, in the wrong state, and only shedding load breaks the loop.

The common thread: **waiting** is what spreads failure. Every pattern below limits how long, how often, or how many callers wait on something that isn't working.

Next, a short check on what you just read.
