# Partitioning, Hot Spots, and Rate Limiting

*Based on* Designing Data-Intensive Applications*, Chapter 6.*

Replication puts the *same* data on several machines. When the data, or the write load, is too big for one machine, you also need **partitioning**: splitting the data so each machine holds a different subset. Partitions are called **shards** in MongoDB and Elasticsearch, **regions** in HBase, **tablets** in Bigtable, and **vnodes** in Cassandra and Riak. The two are usually combined: each partition is replicated to several nodes, and each node holds several partitions.

The goal is to spread data and queries **evenly**. If some partitions get more than their share, partitioning is **skewed**, and an overloaded partition is a **hot spot**.

## Partitioning by key range

Give each partition a continuous range of keys, like the volumes of an encyclopedia: A–Ce, Cf–F, and so on. The boundaries don't have to be even; they adapt to the data.

- ✓ Keys within a partition stay **sorted**, so **range scans** are efficient ("all readings from sensor 42 in March").
- ✗ Some access patterns create hot spots. With timestamp keys, all of today's writes land on one partition. A common fix is to prefix the key with something else, such as the sensor name, so writes spread out at the cost of range queries over time.

HBase, Bigtable, and MongoDB (in range mode) work this way.

## Partitioning by hash of key

Hash each key and give each partition a range of **hashes**. A good hash function (MD5 or Murmur3, *not* a language's built-in `hash()`, which may differ between processes) scatters even similar keys uniformly.

- ✓ Load spreads evenly.
- ✗ Range queries lose their locality: adjacent keys end up on different partitions.

Cassandra compromises with a **compound primary key**. The first column is hashed to choose the partition; the rest sort data within it. That's efficient for "all posts by user 42, newest first."

## Skewed workloads

Hashing can't help when **one key** is hot. A celebrity with 100 million followers posts, and every read and write goes to the same key, so the same partition. Applications must handle this themselves. One technique is to add a random two-digit suffix to the hot key, splitting its writes over 100 keys, at the cost of reading all 100 back. Caches absorb hot *reads* well, as you'll see in the capstone.

## Secondary indexes

Looking up by something other than the primary key ("all red cars") complicates things:

- **Document-partitioned (local) indexes**: each partition indexes only its own documents. Writes stay on one partition, but a query must ask **every** partition and combine the results (**scatter/gather**), so tail latency adds up.
- **Term-partitioned (global) indexes**: the index itself is partitioned by the indexed value, so `color:red` lives on one partition. Reads touch one partition, but a single write may update several, usually asynchronously.

## Rebalancing

Over time, partitions must move between nodes as machines are added or removed. Requirements: share the load fairly afterward, keep serving during the move, and **move no more data than necessary**.

**Don't use hash mod N.** With `node = hash(key) % N`, changing N from 10 to 11 moves almost every key, about 90% of them.

Better strategies:

- **Fixed number of partitions**: create many more partitions than nodes (say 1,000 for 10 nodes). A new node steals a few whole partitions from each existing node; keys never change partition. Used by Riak, Elasticsearch, and Couchbase.
- **Dynamic partitioning**: split a partition when it grows too big, and merge it when it shrinks. Used by HBase and MongoDB.
- **Consistent hashing**: place nodes at points on a hash **ring**. Each key belongs to the first node clockwise from its hash. Adding a node only takes keys from its neighbor, so about **1/N** of the keys move. Each node appears at many points (**virtual nodes**) so the arcs, and the load, even out. Used by Dynamo-style stores and many caches.

You'll build a consistent hashing partitioner in the next lesson.

## Request routing

When a client wants key `user:42`, which node should it ask? This is **service discovery**:

1. Ask **any node**. If it doesn't own the key, it forwards the request (Cassandra and Riak use a **gossip** protocol to share the partition map).
2. Send everything through a **routing tier** that knows the map.
3. Make **clients partition-aware**, so they connect straight to the right node.

Something must hold the authoritative map. Often it's a coordination service like **ZooKeeper** or etcd, which nodes register with and routers watch for changes.

## Rate limiting

Partitioning protects you from *expected* growth. **Rate limiting** protects you from the unexpected: a buggy client in a retry loop, a scraper, or an attacker. It caps how many requests a client (by API key, user, or IP address) may send, and rejects the excess with `429 Too Many Requests`, ideally with a `Retry-After` header.

| Algorithm | How it works | Trade-off |
|---|---|---|
| **Token bucket** | Each client has a bucket of up to B tokens, refilled at R per second. Each request spends one. | Allows short bursts up to B while capping the average rate at R. The most common choice. |
| **Leaky bucket** | Requests join a queue drained at a fixed rate. | Smooth output, but bursts wait or are dropped. |
| **Fixed window** | Count requests per calendar minute. | Simple, but a client can send 2× the limit across a window boundary. |
| **Sliding window** | Weight the previous window's count by how much of it overlaps. | Smooths the boundary problem cheaply. |

With many API servers, the counters must be **shared**, usually in Redis with atomic increments, or kept approximately per server. Put limits early (at the edge or in an API gateway) so rejected requests cost almost nothing. Set them high enough that real users never notice. The simulator's capstone counts real users rejected by an overeager limiter as failures.

## Key terms

| Term | Meaning |
|---|---|
| Partition / shard | A subset of the data on one node (or replica set) |
| Skew / hot spot | Uneven load / one overloaded partition |
| Key-range partitioning | Contiguous key ranges per partition; good for scans |
| Hash partitioning | Ranges of key hashes per partition; even, but no scans |
| Consistent hashing | A hash ring where adding a node moves about 1/N of the keys |
| Scatter/gather | Querying every partition and combining the results |
| Token bucket | Rate limiting with a refilling allowance of requests |
