# Cache Write Patterns

*Chapter 5 · Replication and Caching.*

## Write patterns

### Invalidate on write (with cache-aside)

On a write, update the database, then **delete** the cached copy. The next read misses and loads the fresh value.

Why delete instead of updating the cache with the new value? Because concurrent writers race. Writer A sets the database to 1 and writer B sets it to 2, but their cache updates arrive in the opposite order, and the cache holds 1 forever while the database holds 2. A delete is idempotent and order-insensitive: whatever order deletes arrive in, the next reader loads the current value.

Even deleting leaves a window. A reader misses and loads the *old* value from the database. A writer updates the database and deletes the key. Then the slow reader stores its stale value, which now lives until it expires. Facebook's memcache paper closes the window with **leases**: on a miss, the cache hands the reader a token, and a delete invalidates it, so the cache refuses the stale reader's set. A **TTL** on every entry is the last line of defense: whatever goes wrong, staleness is bounded.

### Write-through

Write to the database and the cache together, on every write. Reads after a write always hit, and the cache is never stale for data written through it. But every write pays for both stores, the cache fills with data that may never be read, and if the two writes aren't atomic (they usually aren't), a failure between them leaves them disagreeing.

### Write-behind (write-back)

Write only to the cache, acknowledge immediately, and write to the database **later**, in batches. It's the write-back policy of chapter 1's page cache, one level up.

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

For keeping many caches and indexes in sync with a database reliably, the best tool comes later: subscribe them to the database's change stream (change data capture, chapter 9).

Next, a short check on what you just read.
