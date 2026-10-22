# Caching Strategies: Patterns, Eviction, and Stampedes

The last two lessons made copies of data on other machines, and showed what it costs when a copy lags behind. A cache is another kind of **copy**: data kept somewhere faster, with no replication log keeping it in sync. Caches take most of the read load off databases, but every copy raises the questions this lesson answers: How does data get into the cache? What happens to the copy when the original changes? What gets thrown out when the cache is full? And what happens when a popular entry disappears and a thousand requests notice at once?

## Where caches live

A request passes through many layers, and almost every one can cache:

| Layer | Example | Typical contents |
|---|---|---|
| Client | Browser cache, mobile app storage | Static files, API responses with `Cache-Control` headers |
| Edge | CDN | Images, scripts, video, cacheable pages |
| Reverse proxy | NGINX, Varnish (lesson 12) | Whole HTTP responses |
| Application, in-process | A dictionary or Caffeine in each server | Hot configuration, small lookup tables |
| Distributed cache | Redis, Memcached | Query results, sessions, computed objects |
| Database | The buffer pool, the OS page cache (lesson 5) | Disk pages |

An **in-process** cache is fastest (no network hop) but each server has its own copy, so N servers hold N copies that go stale independently, and a server restart starts cold. A **distributed** cache is shared and survives app restarts, at the cost of a network round trip (still far cheaper than a database query). Many systems use both: a small in-process cache in front of a large distributed one.

Caching pays off when reads greatly outnumber writes, the same data is read repeatedly (the hit rate is high), and the data is expensive to produce. Lesson 5's arithmetic applies: at a 99% hit rate, the 1% of misses can still dominate the average latency, and the misses all land on the database.

## Read patterns

### Cache-aside (lazy loading)

The application manages the cache itself:

```python
def read(key):
    value = cache.get(key)
    if value is None:            # miss
        value = db.get(key)
        cache.set(key, value)
    return value
```

It's the most common pattern because it's simple and resilient: if the cache is down, reads fall through to the database (slowly, but they work), and only data that's actually read gets cached. The costs: every miss takes three trips (cache, database, cache), and data can go stale in the cache when the database changes.

### Read-through

The same idea, but the **cache** loads misses from the database itself, through a loader you configure. Application code just calls `cache.get(key)`. Many in-process caches and some CDNs work this way.

## Write patterns

### Invalidate on write (with cache-aside)

On a write, update the database, then **delete** the cached copy. The next read misses and loads the fresh value.

Why delete instead of updating the cache with the new value? Because concurrent writers race. Writer A sets the database to 1 and writer B sets it to 2, but their cache updates arrive in the opposite order, and the cache holds 1 forever while the database holds 2. A delete is idempotent and order-insensitive: whatever order deletes arrive in, the next reader loads the current value.

Even deleting leaves a window. A reader misses and loads the *old* value from the database. A writer updates the database and deletes the key. Then the slow reader stores its stale value, which now lives until it expires. Facebook's memcache paper closes the window with **leases**: on a miss, the cache hands the reader a token, and a delete invalidates it, so the cache refuses the stale reader's set. A **TTL** on every entry is the last line of defense: whatever goes wrong, staleness is bounded.

### Write-through

Write to the database and the cache together, on every write. Reads after a write always hit, and the cache is never stale for data written through it. But every write pays for both stores, the cache fills with data that may never be read, and if the two writes aren't atomic (they usually aren't), a failure between them leaves them disagreeing.

### Write-behind (write-back)

Write only to the cache, acknowledge immediately, and write to the database **later**, in batches. It's the write-back policy of lesson 5's page cache, one level up.

- **Fast writes**, and **coalescing**: a counter incremented 1,000 times between flushes becomes one database write.
- **Durability risk**: writes acknowledged but not yet flushed are lost if the cache node dies. Use it only where that's acceptable (view counts, metrics) or where the cache itself is replicated and persistent.
- The pending writes are the **only** copy of the newest data. Reads must check them before the database, even if the cache evicted the entry.

### Write-around

Write only to the database and let reads populate the cache. It's the cache-aside write without the invalidation, so use it only with short TTLs, for data written once and rarely read soon after (log entries, archives).

| Pattern | Write path | Staleness | Write latency | Risk |
|---|---|---|---|---|
| Cache-aside + invalidate | Database, then delete from cache | Brief race windows | Database only | Stale fill race |
| Write-through | Database and cache | Low | Both stores | Partial failure between them |
| Write-behind | Cache now, database later | None in cache; database lags | Cache only | Losing unflushed writes |
| Write-around | Database only | Until TTL | Database only | Stale until expiry |

For keeping many caches and indexes in sync with a database reliably, the best tool comes later: subscribe them to the database's change stream (change data capture, lesson 39).

## Eviction policies

A cache has finite memory. When it's full, inserting a new entry means evicting an old one. The policy decides which.

- **LRU (least recently used)**: evict whatever has gone longest without use. It bets on **temporal locality** and is the default almost everywhere (you built one in lesson 5). Its weakness is **scans**: a batch job reading a million keys once each pushes every genuinely hot key out of the cache.
- **LFU (least frequently used)**: evict whatever has been used the fewest times. Popular keys survive scans because one-off reads never catch up with their counts. Its weaknesses: a key that was popular yesterday keeps its high count forever (real implementations **age** counts over time), and a new key starts with a low count and is evicted before it can prove itself.
- **FIFO** and **random**: cheap and surprisingly decent when access is fairly uniform.
- **TTL-based**: entries expire after a fixed time regardless of use, which bounds staleness rather than memory.
- **Modern hybrids**: **ARC** balances recency and frequency adaptively. **W-TinyLFU** (used by Caffeine) admits a new key only if a compact frequency sketch says it's more popular than the eviction victim. Redis offers approximate LRU and LFU, sampling a few keys rather than tracking exact order.

LRU and LFU can both evict in O(1) with the right data structures (a linked list, or lists of keys bucketed by frequency). For this lesson, correctness matters more than constant factors.

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

A single key can be too hot even for a cache: one celebrity's profile read 1 million times a second overwhelms the one cache node that owns it (lesson 26's skew problem, at the cache tier). Fixes: keep hot keys in an **in-process** cache on every app server, or **replicate** the hot key across several cache nodes under different names and pick one at random.

## Your task

`solution.py` has three parts. `LRUCache` is provided for comparison.

### 1. LFU eviction

`LFUCache(capacity)`: `get(key)` returns the value or `None`, and `put(key, value)` inserts or updates. Both count as a **use**. When inserting a new key into a full cache, evict the key with the fewest uses, breaking ties by evicting the least recently used. A test runs a scan past both caches: LRU loses its hot keys, and yours must keep them.

### 2. Read and write patterns

`cache` has `get(key)` (returning `None` on a miss), `set(key, value)`, and `delete(key)`. `db` has `get(key)` (`None` if the key doesn't exist) and `set(key, value)`.

- `CacheAside.read(key)`: cache first; on a miss, load from the database and fill the cache. Don't cache a key the database doesn't have.
- `CacheAside.write(key, value)`: write the database, then **delete** the cached copy.
- `WriteThrough.write`: write the database and set the cache.
- `WriteBehind.write`: set the cache and remember the write as pending, without touching the database. `flush()` writes each pending key's **latest** value to the database once. `read` must return a pending value even if the cache has dropped it.

### 3. Stampede protection

- `SingleFlight.do(key, fn)`: if no call for `key` is running, run `fn()` and return its result. If one is, wait for it and return the same result, or raise the same exception. Calls for different keys don't wait for each other, and a call after the previous one has finished runs `fn` again. Guard your bookkeeping with a `threading.Lock`, and let waiters block on a `threading.Event`.
- `CoalescingCache.get(key)`: today, 20 readers that miss at once call the loader 20 times. Route the load through a `SingleFlight` so they cause one load.
- `jittered_ttl(ttl, rng, spread=0.1)`: `ttl * (1 + rng.uniform(-spread, spread))`.
- `should_refresh_early(now, expiry, delta, beta, rand)`: the XFetch rule above.

## Key terms

| Term | Meaning |
|---|---|
| Hit rate | The fraction of reads the cache answers |
| Cache-aside | The application loads misses itself and invalidates on write |
| Read-through | The cache loads its own misses |
| Write-through | Every write goes to the database and the cache together |
| Write-behind | Writes go to the cache now and the database later |
| Invalidation | Deleting a cached copy so the next read reloads it |
| LRU / LFU | Evict the least recently / least frequently used key |
| Scan resistance | Hot keys surviving a one-off read of many cold keys |
| Cache stampede | Many simultaneous misses recomputing the same value |
| Single flight | One load per key; concurrent callers share the result |
| TTL jitter | Randomizing expiry times so keys don't expire together |
| Probabilistic early expiration | Refreshing before expiry with rising probability |
