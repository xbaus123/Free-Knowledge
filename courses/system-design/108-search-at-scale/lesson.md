# Search at Scale

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

## Search at scale: Elasticsearch

An Elasticsearch **index** is split into **shards**, each a complete Lucene index, spread across a cluster of nodes:

- The number of **primary shards** is fixed when the index is created. A document goes to shard `hash(_id) % primaries`. This is partitioning with a fixed number of partitions (chapter 6): to grow, you add nodes and move whole shards, never re-hash documents. Changing the shard count means reindexing.
- Each primary has **replica shards** on other nodes. Replicas give failover *and* read capacity: any copy of a shard can answer a search. Search is **read-heavy** (often a hundred searches for each update), so read throughput scales by adding replicas.

A search is a **scatter-gather** in two phases, **query then fetch**:

1. **Query**: the coordinating node sends the query to one copy of every shard. Each shard finds its own top k and returns only ids and scores.
2. **Fetch**: the coordinator merges those lists into the global top k, then fetches the full documents for just those k from the shards that hold them.

Scatter-gather has consequences:

- **Tail latency**: a search is as slow as its slowest shard. With 50 shards, even a 1% chance of a slow shard makes 40% of searches slow (chapter 1's tail latency amplification). Engines hedge by sending duplicate requests to replicas, and set timeouts that return partial results.
- **Deep pagination is expensive**: page 1,000 of 10 results means every shard returns its top 10,010, and the coordinator sorts them all. Use a cursor (`search_after`) instead of `from` and `size`.
- **Distributed scoring is approximate**: each shard computes IDF from its own documents only, so with few documents per shard, scores can differ slightly depending on where a document landed.

### Search is derived data

A search index is almost never the **system of record**. The source of truth stays in a database. The index is a **derived** view, rebuilt from that source whenever its analyzers or mappings change. Keeping it in sync reliably is a classic problem: dual-writing from the application loses updates whenever the index is down. Chapter 9 fixes that with change data capture.

### Beyond keywords

Keyword search fails when users and documents use different words for the same idea ("cheap flights" vs. "low-cost airfare"). **Vector search** embeds documents and queries as points in a high-dimensional space, using a machine-learning model, and finds the **nearest neighbors** to the query. Exact nearest-neighbor search in hundreds of dimensions is too slow, so engines use **approximate** indexes like **HNSW** (hierarchical navigable small-world graphs). Many systems now run **hybrid search**: BM25 and vector results, merged into one ranking. **Geospatial** search ("restaurants within 2 km") uses yet another family of indexes, such as R-trees and geohashes, which turn two-dimensional proximity into something an index can look up.

Next, a short check on what you just read.
