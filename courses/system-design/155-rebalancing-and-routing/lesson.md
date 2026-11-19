# Rebalancing and Request Routing

*Chapter 6 · Partitioning and Geography.*

## Rebalancing

Over time, partitions must move between nodes as machines are added or removed. Requirements: share the load fairly afterward, keep serving during the move, and **move no more data than necessary**.

**Don't use hash mod N.** With `node = hash(key) % N`, changing N from 10 to 11 moves almost every key, about 90% of them.

Better strategies:

- **Fixed number of partitions**: create many more partitions than nodes (say 1,000 for 10 nodes). A new node steals a few whole partitions from each existing node; keys never change partition. Used by Riak, Elasticsearch, and Couchbase.
- **Dynamic partitioning**: split a partition when it grows too big, and merge it when it shrinks. Used by HBase and MongoDB.
- **Consistent hashing**: place nodes at points on a hash **ring**. Each key belongs to the first node clockwise from its hash. Adding a node only takes keys from its neighbor, so about **1/N** of the keys move. Each node appears at many points (**virtual nodes**) so the arcs, and the load, even out. Used by Dynamo-style stores and many caches.

You'll build a consistent hashing partitioner right after this reading's check.

## Request routing

When a client wants key `user:42`, which node should it ask? This is **service discovery**:

1. Ask **any node**. If it doesn't own the key, it forwards the request (Cassandra and Riak use a **gossip** protocol to share the partition map).
2. Send everything through a **routing tier** that knows the map.
3. Make **clients partition-aware**, so they connect straight to the right node.

Something must hold the authoritative map. Often it's a coordination service like **ZooKeeper** or etcd, which nodes register with and routers watch for changes.

Next, a short check on what you just read.
