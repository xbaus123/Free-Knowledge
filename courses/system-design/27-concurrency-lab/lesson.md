# Operating Systems and Hardware: Threads, Locks, and the Memory Hierarchy

*Chapter 1 · Foundations.*

Put the last four readings to work: fix a race, fix a deadlock, and build an LRU page cache with write-back.

## Your task

`solution.py` has three parts.

### 1. Fix the race

`Counter.increment()` does a read-modify-write. The `time.sleep(0)` stands in for the scheduler switching threads at the worst moment. Eight threads each call `increment()` 500 times, and the total must be exactly 4,000. Protect the critical section with a `threading.Lock`, and keep the `sleep(0)` inside it.

### 2. Fix the deadlock

`transfer(source, target, amount)` locks the source, then the target. Threads transferring in opposite directions deadlock. Make every thread take the two locks in the same order, by account `id`. Also raise `InsufficientFunds`, changing nothing, when the source can't cover the amount. Check the balance while you hold both locks, or another thread could spend the money between your check and your update.

The tests run transfers on several threads and fail if any thread is still stuck after a few seconds, if money appears or disappears, or if an account goes negative.

### 3. A page cache

`PageCache(capacity, disk)` keeps up to `capacity` pages in memory in front of `disk`, whose `read(page)` and `write(page, data)` are slow.

- `read(page)`: return cached data on a **hit**. On a **miss**, read from disk and cache it. Count `hits` and `misses`.
- When the cache is over capacity, evict the **least recently used** page. Both reads and writes count as uses.
- `write(page, data)`: **write-back**. Update the page in memory and remember that it's **dirty** (changed since it was last on disk). Don't touch the disk yet.
- Evicting a dirty page writes it to disk first. Evicting a clean page needs no write.
- `flush()`: write every dirty page to disk once, and mark it clean.

`collections.OrderedDict` makes LRU easy:

```python
from collections import OrderedDict
pages = OrderedDict()
pages.move_to_end(key)         # mark as most recently used
pages.popitem(last=False)      # remove the least recently used
```

Then `effective_access_ns(hit_rate, cache_ns, backing_ns)` computes the formula above.

Use the **Scratchpad** to watch the race happen: run the original `Counter` on eight threads and print the total a few times.

## Key terms

| Term | Meaning |
|---|---|
| Process / thread | A program with its own memory / a line of execution sharing its process's memory |
| Context switch | The scheduler moving a core from one thread to another |
| Race condition | A result that depends on how threads happen to interleave |
| Critical section | Code that only one thread may run at a time |
| Lock (mutex) | Lets one thread at a time into a critical section |
| Deadlock | Threads each waiting for a lock another one holds, forever |
| Lock ordering | Taking locks in one global order so no waiting cycle can form |
| Locality | Recently used and nearby data tends to be used next |
| LRU | Evict whatever was used least recently |
| Write-back | Keep writes in memory and write them to the slower level later |
| fsync | Force buffered writes onto durable storage |

Next, you'll look at how programs on different machines talk to each other: HTTP, REST, RPC, and GraphQL.
