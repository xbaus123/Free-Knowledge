# Skew and Secondary Indexes

*Chapter 6 · Partitioning and Geography.*

## Skewed workloads

Hashing can't help when **one key** is hot. A celebrity with 100 million followers posts, and every read and write goes to the same key, so the same partition. Applications must handle this themselves. One technique is to add a random two-digit suffix to the hot key, splitting its writes over 100 keys, at the cost of reading all 100 back. Caches absorb hot *reads* well, as you'll see in the capstone.

## Secondary indexes

Looking up by something other than the primary key ("all red cars") complicates things:

- **Document-partitioned (local) indexes**: each partition indexes only its own documents. Writes stay on one partition, but a query must ask **every** partition and combine the results (**scatter/gather**), so tail latency adds up.
- **Term-partitioned (global) indexes**: the index itself is partitioned by the indexed value, so `color:red` lives on one partition. Reads touch one partition, but a single write may update several, usually asynchronously.

Next, a short check on what you just read.
