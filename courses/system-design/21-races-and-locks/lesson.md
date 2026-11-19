# Race Conditions and Locks

*Chapter 1 · Foundations.*

## Race conditions

Shared memory is convenient and dangerous. Consider `count += 1`. It looks like one step, but it's three: read `count`, add 1, write `count` back. Two threads can interleave like this:

```text
Thread A                Thread B
read count  (5)
                        read count  (5)
write count (6)
                        write count (6)     one increment is lost
```

This is a **race condition**: the result depends on the timing of the interleaving. Races are maddening because they're rare. The code works in testing and fails once a day in production under load. The problematic pattern is **read-modify-write** on shared data, and you'll meet it again at database scale as the **lost update** (chapter 7).

## Locks

A **lock** (or **mutex**, for mutual exclusion) lets only one thread at a time into a **critical section**:

```python
lock = threading.Lock()

with lock:              # wait until no one else holds it, then take it
    count = count + 1   # only one thread at a time runs this
                        # released when the block ends, even on an exception
```

Locks make code correct, but they have costs:

- **Contention**: threads waiting on a lock aren't doing work. A lock held too long turns parallel code into serial code.
- **Granularity**: one big lock is simple but slow. Many small locks are fast but easy to get wrong.

Related tools you'll see: **read-write locks** (many readers or one writer), **semaphores** (at most *n* holders), **condition variables** (wait until something changes), and **atomic operations** (a single hardware instruction like compare-and-swap, with no lock at all).

Next, a short check on what you just read.
