# Caching Strategies: Patterns, Eviction, and Stampedes

*Chapter 5 · Replication and Caching.*

Build what the caching readings described: LFU eviction, cache-aside, write-through, and write-behind, and stampede protection.

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
