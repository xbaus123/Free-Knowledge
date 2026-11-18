# Keeping Copies Consistent

*Chapter 1 · Part 5: Resource Management.*

Caching means the same data can exist in **several places at once**. That's great for speed, and a headache for correctness.

## Data "A" moves up the hierarchy

Suppose a program increments an integer **A** stored in a file on disk:

```
 [ hard disk ] ──A──► [ main memory ] ──A──► [ cache ] ──A──► [ hardware register ]
```

1. The block holding A is copied from disk to main memory.
2. A is copied into the CPU cache.
3. A is copied into a register, and incremented there.

Now **A has a different value in different places**. Only after the new value is written back from the register, to the cache, to memory, and finally to disk, are all the copies the same again.

## Multitasking: use the most recent value

With one process, that's fine: it always reads the copy at the top. But with multitasking, **every process that wants A must get the most recently updated value, no matter where in the hierarchy it's stored**.

## Multiprocessors: cache coherency

On a multiprocessor it's harder. Each CPU has its **own cache** (remember the SMP diagram), so A could be in CPU 0's cache *and* CPU 1's cache. If CPU 0 updates its copy, CPU 1's copy is instantly stale.

The fix is **cache coherency**, provided **in hardware**: it makes sure that when one CPU updates a value, **all the other CPUs' caches** see the change (usually by invalidating or updating their copies). That way all CPUs have the most recent value in their cache.

## Distributed systems: even harder

In a **distributed environment** the situation is **even more complex**: **several copies (replicas) of a datum can exist on different computers**, connected by a network that can be slow or broken. Keeping replicas consistent there is a whole topic in distributed systems.

| Setting | Copies of A | Who keeps them consistent |
|---|---|---|
| One process | Disk, memory, cache, register | The normal write-back path |
| Multitasking | Same | OS and hardware: always use the newest copy |
| Multiprocessor | One per CPU cache, plus memory | **Cache-coherency hardware** |
| Distributed | Replicas on many machines | Distributed algorithms (later chapters) |

Next, a check on consistency.
