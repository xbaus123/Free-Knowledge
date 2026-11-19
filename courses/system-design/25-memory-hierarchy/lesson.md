# The Memory Hierarchy

*Chapter 1 · Foundations.*

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

Disks and SSDs are far faster reading and writing **sequentially** (one long run of blocks) than **randomly** (scattered blocks). On a spinning disk, every random access pays a physical seek. On an SSD the gap is smaller but still large. Many storage engines are designed around this. The append-only log you'll build in chapter 3 turns every write into a sequential one.

### Volatility and durability

RAM is **volatile**: power loss erases it. The operating system's **page cache** keeps recently used disk pages in RAM and holds writes there too, writing them to disk later (**write-back**). That's fast, but a crash can lose writes your program believed were saved. A database that promises **durability** calls `fsync` to force its data onto disk before telling you a write succeeded. That's one reason commits are slow, and why later chapters care so much about logs.

Next, a short check on what you just read.
