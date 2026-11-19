# Eviction Policies

*Chapter 5 · Replication and Caching.*

## Eviction policies

A cache has finite memory. When it's full, inserting a new entry means evicting an old one. The policy decides which.

- **LRU (least recently used)**: evict whatever has gone longest without use. It bets on **temporal locality** and is the default almost everywhere (you built one in chapter 1). Its weakness is **scans**: a batch job reading a million keys once each pushes every genuinely hot key out of the cache.
- **LFU (least frequently used)**: evict whatever has been used the fewest times. Popular keys survive scans because one-off reads never catch up with their counts. Its weaknesses: a key that was popular yesterday keeps its high count forever (real implementations **age** counts over time), and a new key starts with a low count and is evicted before it can prove itself.
- **FIFO** and **random**: cheap and surprisingly decent when access is fairly uniform.
- **TTL-based**: entries expire after a fixed time regardless of use, which bounds staleness rather than memory.
- **Modern hybrids**: **ARC** balances recency and frequency adaptively. **W-TinyLFU** (used by Caffeine) admits a new key only if a compact frequency sketch says it's more popular than the eviction victim. Redis offers approximate LRU and LFU, sampling a few keys rather than tracking exact order.

LRU and LFU can both evict in O(1) with the right data structures (a linked list, or lists of keys bucketed by frequency). For the lab, correctness matters more than constant factors.

Next, a short check on what you just read.
