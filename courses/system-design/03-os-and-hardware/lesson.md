# Operating Systems and Hardware: Threads, Locks, and the Memory Hierarchy

*Part I · Foundations.*

Before you spread work across many machines, you need to know what one machine does well and badly. Two facts shape almost every design in this course: **many things happen at once**, so shared data needs protection, and **storage is a hierarchy**, where each level down is bigger, cheaper, and dramatically slower.

## Processes and threads

A **process** is a running program with its own **address space**: its own view of memory, its own open files, its own crash. The operating system keeps processes apart, so one can't scribble over another's memory.

A **thread** is one sequence of execution *inside* a process. A process can run many threads, and they all share its memory.

| | Processes | Threads |
|---|---|---|
| Memory | Separate; talk through pipes, sockets, or files | Shared; any thread can read or write any variable |
| Cost to create and switch | Higher | Lower |
| A crash takes down | One process | Every thread in the process |
| Typical use | Isolation: one worker per request in older web servers, browser tabs | Concurrency within one service: a thread pool handling requests |

The **scheduler** decides which thread runs on each CPU core and switches between them (a **context switch**) many times a second. A switch can happen between *any* two instructions. Your code doesn't get a say.

Two words people mix up:

- **Concurrency**: several tasks in progress at once, interleaved. One core can do it by switching.
- **Parallelism**: several tasks *executing* at the same instant, on different cores.

Python's standard interpreter has a **global interpreter lock (GIL)** that lets only one thread run Python code at a time. That limits parallelism, but not concurrency: threads still interleave, so every bug in this lesson happens in Python too.

## Race conditions

Shared memory is convenient and dangerous. Consider `count += 1`. It looks like one step, but it's three: read `count`, add 1, write `count` back. Two threads can interleave like this:

```text
Thread A                Thread B
read count  (5)
                        read count  (5)
write count (6)
                        write count (6)     one increment is lost
```

This is a **race condition**: the result depends on the timing of the interleaving. Races are maddening because they're rare. The code works in testing and fails once a day in production under load. The problematic pattern is **read-modify-write** on shared data, and you'll meet it again at database scale as the **lost update** (lesson 21).

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

## Deadlock

Take two bank accounts, each with its own lock. A transfer locks the source, then the target. Now two transfers run at once in opposite directions:

```text
Thread A: transfer(x → y)         Thread B: transfer(y → x)
lock x                            lock y
wait for y ...                    wait for x ...       forever
```

Each holds the lock the other needs. Neither will ever let go. That's a **deadlock**. It needs four conditions together: mutual exclusion, holding one resource while waiting for another, no forcible taking of locks, and a **cycle** of waiting. Break any one and deadlock is impossible. The usual fix breaks the cycle with **lock ordering**: every thread takes locks in the same global order, such as lowest account id first. Then no cycle can form.

Databases face the same problem with row locks. They detect the cycle and abort one transaction, which your application must retry.

## The memory hierarchy

Every machine stacks storage in levels. Closer to the CPU means faster, smaller, and more expensive per byte:

| Level | Typical size | Access time | Survives power loss? |
|---|---|---|---|
| CPU registers | Bytes | < 1 ns | No |
| L1 / L2 / L3 caches | KB to tens of MB | 1 to 40 ns | No |
| RAM | Gigabytes | ~100 ns | No |
| SSD | Terabytes | ~100 µs random read | Yes |
| Spinning disk | Terabytes | ~10 ms random read | Yes |
| Another machine in the data center | Unlimited | ~0.5 ms round trip | Depends |

Scale it up so 1 ns is one second: a RAM access takes under two minutes, an SSD read takes about a day, and a spinning disk seek takes nearly four months. That's why systems work so hard to keep hot data in memory.

### Caches and locality

Every level acts as a **cache** for the level below. A cache works because of **locality**:

- **Temporal locality**: data used recently is likely to be used again soon.
- **Spatial locality**: data near what you just used is likely to be used next, so storage reads in whole **blocks** or **pages** (often 4 KB), not single bytes.

When a cache is full, it must **evict** something. **Least recently used (LRU)** eviction bets on temporal locality: throw out whatever has gone longest without use.

The average cost of an access depends overwhelmingly on the **miss rate**:

> effective time = hit rate × cache time + miss rate × (cache time + backing time)

With RAM at 100 ns in front of an SSD at 100 µs, a 99% hit rate averages 1,100 ns. That's eleven times slower than RAM, caused entirely by 1% of accesses.

### Sequential vs. random

Disks and SSDs are far faster reading and writing **sequentially** (one long run of blocks) than **randomly** (scattered blocks). On a spinning disk, every random access pays a physical seek. On an SSD the gap is smaller but still large. Many storage engines are designed around this. The append-only log you'll build in lesson 12 turns every write into a sequential one.

### Volatility and durability

RAM is **volatile**: power loss erases it. The operating system's **page cache** keeps recently used disk pages in RAM and holds writes there too, writing them to disk later (**write-back**). That's fast, but a crash can lose writes your program believed were saved. A database that promises **durability** calls `fsync` to force its data onto disk before telling you a write succeeded. That's one reason commits are slow, and why the next lessons care so much about logs.

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

Next, you'll look at how programs on different machines talk to each other: REST, RPC, and GraphQL.
