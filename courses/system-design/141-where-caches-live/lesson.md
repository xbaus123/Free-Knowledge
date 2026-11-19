# Where Caches Live, and Read Patterns

*Chapter 5 · Replication and Caching.*

The replication readings made copies of data on other machines, and showed what it costs when a copy lags behind. A cache is another kind of **copy**: data kept somewhere faster, with no replication log keeping it in sync. Caches take most of the read load off databases, but every copy raises the questions the caching readings answer: How does data get into the cache? What happens to the copy when the original changes? What gets thrown out when the cache is full? And what happens when a popular entry disappears and a thousand requests notice at once?

## Where caches live

A request passes through many layers, and almost every one can cache:

| Layer | Example | Typical contents |
|---|---|---|
| Client | Browser cache, mobile app storage | Static files, API responses with `Cache-Control` headers |
| Edge | CDN | Images, scripts, video, cacheable pages |
| Reverse proxy | NGINX, Varnish (chapter 2) | Whole HTTP responses |
| Application, in-process | A dictionary or Caffeine in each server | Hot configuration, small lookup tables |
| Distributed cache | Redis, Memcached | Query results, sessions, computed objects |
| Database | The buffer pool, the OS page cache (chapter 1) | Disk pages |

An **in-process** cache is fastest (no network hop) but each server has its own copy, so N servers hold N copies that go stale independently, and a server restart starts cold. A **distributed** cache is shared and survives app restarts, at the cost of a network round trip (still far cheaper than a database query). Many systems use both: a small in-process cache in front of a large distributed one.

Caching pays off when reads greatly outnumber writes, the same data is read repeatedly (the hit rate is high), and the data is expensive to produce. Chapter 1's arithmetic applies: at a 99% hit rate, the 1% of misses can still dominate the average latency, and the misses all land on the database.

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

Next, a short check on what you just read.
