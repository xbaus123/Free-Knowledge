# Cache Stampedes and Hot Keys

*Chapter 5 · Replication and Caching.*

## Cache stampedes

Suppose a key is read 10,000 times a second and takes 200 ms to compute from the database. It expires. In the 200 ms before anyone repopulates it, roughly 2,000 requests miss, and **every one of them** queries the database for the same thing. The database, sized for a 99% hit rate, receives a burst of identical expensive queries and slows down, which makes each recompute slower, which lets even more requests miss. This is a **cache stampede**, also called the **thundering herd** or **dogpile** effect. Variants:

- **Cold start**: a cache restart or a new cache node starts empty, and *every* key misses at once.
- **Synchronized expiry (avalanche)**: keys loaded at the same moment with the same TTL expire at the same moment.
- **Penetration**: requests for keys that don't exist always miss, because there's nothing to cache. Attackers can exploit this.

Defenses, usually combined:

1. **Request coalescing (single flight)**: when many requests miss on the same key at once, only the first loads it. The rest wait for that load and share its result. Go's `singleflight` package is the standard example. Within one server this is just a lock per key. Across servers, a **lease** or a short-lived lock in the cache itself plays the same role: only the lease holder recomputes, and everyone else briefly waits or serves the stale value.
2. **TTL jitter**: add a random ±10% to every TTL so keys written together expire at different times.
3. **Stale-while-revalidate**: keep serving the expired value while one request refreshes it in the background. Users see slightly stale data instead of a slow page. HTTP has a `Cache-Control: stale-while-revalidate` directive for exactly this.
4. **Probabilistic early expiration (XFetch)**: refresh *before* expiry, with a probability that rises as expiry approaches. Each reader independently decides to recompute when
   > now − delta × beta × ln(rand) ≥ expiry

   where *delta* is how long recomputing takes, *beta* tunes eagerness (1 is typical, and 0 disables it), and *rand* is uniform in (0, 1]. Since ln(rand) ≤ 0, the left side is "now, pushed forward by a random amount, on average delta × beta." Far from expiry, almost no one refreshes. Close to it, someone almost certainly does, and usually only one or two readers, before the key ever expires.
5. **Negative caching**: cache "not found" (briefly) so missing keys stop reaching the database.
6. **Warm-up**: prefill a new cache from a snapshot or from the hottest keys before sending it traffic.

### Hot keys

A single key can be too hot even for a cache: one celebrity's profile read 1 million times a second overwhelms the one cache node that owns it (chapter 6's skew problem, at the cache tier). Fixes: keep hot keys in an **in-process** cache on every app server, or **replicate** the hot key across several cache nodes under different names and pick one at random.

Next, a short check on what you just read.
