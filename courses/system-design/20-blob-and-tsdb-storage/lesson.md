# Blob and Time-Series Storage: Object Stores, Erasure Coding, and TSDBs

*Based on* Designing Data-Intensive Applications*, Chapters 3 and 10.*

The storage engines you've built so far store **records**: keys and values of a few bytes to a few kilobytes, read and updated at random. Two workloads break that shape completely:

- **Blobs**: photos, videos, backups, log archives, machine-learning datasets. Megabytes to terabytes each, written once, read whole or in ranges, almost never modified.
- **Time series**: metrics, sensor readings, stock ticks. Billions of tiny `(timestamp, value)` points, arriving in time order, never updated, queried in time ranges, and worth less the older they get.

Each gets its own kind of storage system, and each takes ideas you've already met (immutable files, content hashing, column storage, compaction) to an extreme. This lesson covers both: **object stores** like Amazon S3, and **time-series databases (TSDBs)** like Prometheus.

## Part A: Object storage

### Why not the database, or a filesystem?

You *can* put a 20 MB video in a database column. It's a bad idea. Every copy of the database now carries it: the buffer pool caches it at the expense of hot rows, the replication log ships it to every follower (lesson 23), every backup copies it, and every migration rewrites it. Databases also cap value sizes and aren't built to stream gigabytes. The standard pattern is to keep the **blob** in an object store and the **pointer** (its key) plus searchable metadata in the database.

A distributed filesystem with POSIX semantics (directories, renames, locks, in-place overwrites, appends) is expensive to scale, because every one of those operations needs coordination across machines. Object stores get their scale by **giving most of that up**.

### The object model

- A **bucket** is a namespace, and an **object** is a key, some bytes, and metadata (content type, custom headers).
- The namespace is **flat**. `logs/2026/10/01.gz` is just a key that happens to contain slashes. "Folders" are an illusion created by **listing** with a prefix and a **delimiter**: list `logs/` with delimiter `/`, and the store rolls up every key with another slash after the prefix into one **common prefix**, `logs/2026/`. Renaming a "folder" means copying every object under it.
- Objects are **immutable**: a `PUT` writes the whole object at once. There's no partial update and no append. Writing the same key again replaces the object atomically, so readers see the old version or the new one, never a mix.
- `GET` can read a **byte range**, which is how video players seek and download tools fetch pieces in parallel. `HEAD` returns the metadata without the data.
- Each object has an **ETag**, a fingerprint of its content (for simple uploads, the MD5 of its bytes), so clients can check integrity and make conditional requests ("only if it changed").

On top of that, object stores add **versioning** (keep every version of a key), **lifecycle rules** (move objects to cheaper storage classes after 30 days, delete after a year), **storage classes** trading retrieval latency for price (from milliseconds to hours, for archival tiers), and **presigned URLs**: a URL signed with a key that lets a client upload or download one object directly for a limited time, without its traffic passing through your servers or your servers holding its credentials (lesson 13).

S3 has offered strong read-after-write consistency since December 2020. Before that, overwrites and listings were only eventually consistent, and a `GET` right after an overwrite could return the old object, a lagging-replica problem at planetary scale.

### Inside an object store: metadata versus data

Every object store separates two very different jobs:

1. The **metadata service** maps `(bucket, key)` to an object record: size, ETag, version, user metadata, and the **list of chunks** that hold the data, with their locations. It's a partitioned, replicated key-value store. It's kept **sorted by key** so `LIST` with a prefix is a range scan, which makes it range-partitioned (lesson 26). Range partitioning has the usual hot-spot problem, which is why S3 documents per-prefix request rates (thousands of requests per second per prefix) and splits busy prefixes automatically.
2. **Data nodes** store **chunks**: the object's bytes cut into fixed-size pieces, typically several megabytes each, spread across disks, machines, and data centers.

Chunking buys a lot:

- **Parallelism**: a 10 GB object is hundreds of chunks on hundreds of disks, read or written at the combined speed of all of them.
- **Ranged reads**: a range touches only the chunks that hold it.
- **Multipart uploads**: a client uploads a big object as numbered parts, in parallel and in any order, retrying only failed parts, then calls *complete* to stitch them together. In S3, the ETag of a multipart object is not the MD5 of its bytes, but the MD5 of the parts' MD5s with `-N` appended, where N is the number of parts.

Many systems also name chunks by a **hash of their content** (**content addressing**), as Git does for files:

- Identical chunks are stored once (**deduplication**): a thousand backups of a mostly unchanged disk share most of their chunks.
- Every read can verify its chunk against its name, catching silent disk corruption.
- A chunk never changes, so it can be cached and replicated without invalidation.

Shared chunks need **garbage collection**. Deleting an object removes its metadata record, and a chunk's space is reclaimed only once no object refers to it, tracked by reference counts or by periodically marking every chunk still in use and sweeping the rest. That's why a delete is fast but storage bills shrink later.

The write path follows a simple rule that keeps the store consistent through crashes: **write the data first, then commit the metadata**. Chunks are streamed to data nodes and made durable, and only then is the object record created or swapped to point at them. A crash midway leaves orphaned chunks for the garbage collector, never a record pointing at missing data.

### Durability: replication versus erasure coding

Disks fail constantly at this scale: with a million disks and a 1% annual failure rate, about 27 die every day. The store must lose nothing.

**Replication** keeps 3 copies of each chunk in different failure domains. It's simple, reads are fast, and repairing a lost copy means copying one chunk. But it stores **3 bytes for every byte**: 200% overhead.

**Erasure coding** does better. Split a chunk into **k data shards**, and compute **m parity shards** from them, such that **any k of the k + m shards** can rebuild the original. Store each shard on a different disk or rack:

| Scheme | Storage overhead | Failures survived | Repair cost |
|---|---|---|---|
| 3× replication | 200% | 2 | Copy 1 shard |
| XOR parity, k + 1 (RAID 5 style) | 1/k (25% for k = 4) | 1 | Read k shards |
| Reed-Solomon (6, 3) | 50% | 3 | Read 6 shards |
| Reed-Solomon (10, 4) | 40% | 4 | Read 10 shards |

The simplest erasure code is **XOR parity**: the parity shard is the byte-by-byte XOR of the k data shards. XOR is its own inverse, so XORing the parity with the k − 1 surviving shards gives back the lost one. It survives exactly one loss. **Reed-Solomon** codes generalize this to m parity shards by treating the data as coefficients of polynomials over a finite field: k values determine a polynomial of degree k − 1, so any k of its k + m evaluations rebuild it.

Erasure coding's costs are the reason replication hasn't disappeared:

- **Repair is expensive**: rebuilding one lost shard reads k shards over the network. Systems like Azure's **local reconstruction codes** add extra parity over small groups, so common single failures read fewer shards.
- **Degraded reads are slow**: reading data whose shard is on a dead disk means fetching and decoding k other shards.
- **CPU** for encoding and decoding, and small objects split into tiny shards are inefficient. Stores often keep new, hot data replicated and erasure-code it once it cools, and pack small objects into large **volumes** first. Facebook's Haystack and f4 systems did exactly this for photos.

Cloud object stores advertise durability like 99.999999999% (eleven nines) per year. It comes from erasure coding across data centers, plus constant **scrubbing** (re-reading every shard in the background to find corruption early) and fast repair, because data is lost only if too many shards fail *before* repair finishes.

### Object stores in system design

- **Uploads**: the client asks your API for a presigned URL and uploads directly to the store. The API servers never touch the bytes.
- **Delivery**: put a CDN (lesson 28) in front. Immutable objects with versioned keys cache perfectly.
- **Data lakes**: analytical data lives as columnar Parquet files (lesson 16) in object storage, with table formats like Apache Iceberg and Delta Lake adding transactions on top. Batch jobs (lesson 38) read immutable inputs and write new outputs.
- **Cheap durable backing for other systems**: Kafka tiered storage, database backups, and long-term metrics (below) all offload old data to object storage.

## Part B: Time-series databases

### The workload

A time series is a sequence of `(timestamp, value)` points for one **series**, identified by a metric name and labels, like `http_requests_total{service="api", status="500"}` (lesson 40). The workload has a distinctive shape:

- **Writes dominate**, and arrive at a huge, steady rate. 10,000 servers each exposing 500 metrics, scraped every 15 seconds, is 333,000 points per second, around the clock.
- Points arrive **nearly in time order**, and are almost **never updated or deleted** individually.
- Reads scan **time ranges** ("the last hour") and **aggregate across series** ("total error rate across all API servers").
- Recent data is queried constantly at full detail. Old data is queried rarely, at coarse resolution.

A general-purpose database with a row per point pays per-row overhead (a full timestamp, the labels, a row header) and an index update per insert. A log-structured engine (lesson 18) handles the write rate better. TSDBs go further and exploit the workload's regularity.

### Layout: series, blocks, and columns

Prometheus's storage engine is a good model of the design:

- An **inverted index** maps each label pair to the ids of series that have it, exactly the structure from lesson 19. A query for `{service="api", status="500"}` intersects two postings lists to find its series.
- Recent data lives in an in-memory **head block**, protected by a write-ahead log. Each series' points are appended to its own **chunk**.
- Every two hours, the head is written out as an immutable **block**: a directory of compressed chunks plus its own index. Background **compaction** merges small blocks into larger ones covering longer time ranges.
- **Retention** deletes whole blocks once they're older than the limit. There are no per-point tombstones, so dropping a month of data is as cheap as deleting a directory.

Within a chunk, timestamps and values are stored and compressed **separately**, as columns: a column of timestamps that rise steadily, and a column of values that change slowly.

### Gorilla compression

A raw point takes 16 bytes: an 8-byte timestamp and an 8-byte float. Facebook's **Gorilla** paper (2015) compressed them to about **1.37 bytes per point** on its production data, using two observations.

**Timestamps are regular.** Scrapes happen every 15 seconds, so consecutive timestamps differ by 15, again and again. Store the first timestamp in full, then the first **delta** (the difference), then for each later point only the **delta of deltas**: how much this delta differs from the last one. A perfectly regular series is all zeros. A variable-length code then spends almost nothing on zeros and little on small jitter:

| Delta of deltas | Bits stored |
|---|---|
| 0 | 1 (`0`) |
| −63 to 64 | 2 + 7 (`10` and the value) |
| −255 to 256 | 3 + 9 (`110` and the value) |
| −2,047 to 2,048 | 4 + 12 (`1110` and the value) |
| Anything else | 4 + 32 (`1111` and the value) |

The first timestamp takes 64 bits and the first delta 14. After that, a steady series costs 1 bit per timestamp.

**Values change slowly.** XOR each value's 64-bit floating-point representation with the previous value's. If the value didn't change, the XOR is zero, stored as a single `0` bit. If it changed a little, the two floats share their sign, exponent, and leading mantissa bits, so the XOR has long runs of **leading and trailing zeros**. Gorilla stores only the count of leading zeros and the short run of meaningful bits in between, and reuses the previous point's run boundaries when they still fit. About half of Gorilla's values compressed to a single bit.

Both tricks need the points decoded **in sequence**, which is fine for range scans but rules out jumping to an arbitrary point. That's why chunks are small (around 120 points, or two hours): to read a point, decode its chunk from the start.

### Downsampling and retention

Nobody needs 15-second resolution for last year's CPU usage. **Downsampling** rolls raw points up into coarser buckets, and **retention tiers** keep each resolution for a different time:

| Resolution | Kept for | Used for |
|---|---|---|
| Raw (15 s) | 15 days | Debugging today's incident |
| 5-minute rollups | 90 days | Week-over-week comparisons |
| 1-hour rollups | 5 years | Capacity planning and trends |

What a rollup stores matters. Store **min, max, sum, and count** for each bucket, not just the average. Averages can't be combined correctly without counts (the average of two averages is wrong when buckets hold different numbers of points), and the max is what reveals a spike that an average smooths away. Percentiles can't be rolled up from percentiles at all, so roll up histogram buckets instead (lesson 40).

Prometheus does this with recording rules, and TimescaleDB with **continuous aggregates** that update incrementally as data arrives. Long-term metrics systems like Thanos and Grafana Mimir upload compacted blocks to an **object store** and downsample them there, joining the two halves of this lesson: the TSDB for recent, hot data, the object store for cheap, durable history.

### Picking a TSDB

- **Prometheus**: pull-based monitoring, a single node per server, with Thanos, Mimir, or Cortex for scale and long-term storage.
- **InfluxDB** and **VictoriaMetrics**: purpose-built engines, push or pull, high compression.
- **TimescaleDB**: a PostgreSQL extension that partitions tables by time into **chunks** automatically, keeping SQL, joins, and transactions.
- **ClickHouse** and other columnar warehouses: often used for time series with high-cardinality labels, like events per user.

In all of them, the failure mode to watch is **cardinality**: every distinct label combination is a separate series with its own index entries and chunks, so a label with unbounded values (user ids, request ids) multiplies memory use until the database falls over.

## Your task

`solution.py` has three parts.

### 1. An object store

`ObjectStore(chunk_size)` keeps metadata and data apart:

- `self.objects` maps `(bucket, key)` to `{"size", "etag", "chunks", "metadata"}`, where `chunks` lists the object's chunk hashes in order.
- `self.chunks` maps a chunk's SHA-256 hex digest to its bytes, each stored **once**, and `self.refs` counts how many object chunks use each.
- `_object(bucket, key)` (done) looks up a record or raises `NoSuchKey`, and `_read(digest)` (done) reads a chunk and counts it in `self.chunk_reads`.

Implement:

- `put(bucket, key, data, metadata=None)`: cut the data into `chunk_size` pieces (the last may be shorter), store each new chunk by its SHA-256 hex digest, and record the object. The ETag is the MD5 hex digest of the whole data, and `put` returns it. Replacing an object releases the old version's chunks **after** recording the new one, since they may share chunks.
- `head(bucket, key)`: `{"size", "etag", "metadata"}`, without reading any chunk.
- `get(bucket, key, start=0, end=None)`: the bytes from `start` up to `end` (the end of the object if `None`, and never past it), reading **only** the chunks the range overlaps. An empty range is `b""`.
- `delete(bucket, key)`: remove the object, if it exists, and release its chunks.
- `_release(hashes)`: subtract one reference from each chunk, deleting chunks (from `chunks` and `refs`) that reach zero.
- `list(bucket, prefix="", delimiter=None)`: returns `(keys, common_prefixes)`, both sorted. Without a delimiter, `keys` is every key in the bucket starting with `prefix`. With one, a key that contains the delimiter **after** the prefix goes into common prefixes instead, cut just after that delimiter, once per distinct prefix.

### 2. Erasure coding

`split(data, k)` (done) cuts data into k equal shards, padding with zero bytes.

- `parity(shards)` returns the byte-by-byte XOR of equal-length shards.
- `recover(shards, parity_shard)` takes the shards with exactly one replaced by `None`, and returns the full list with it rebuilt. Raise `ValueError` if the number of `None`s isn't one.

### 3. Time series

- `encode_timestamps(ts)` returns `[t0, t1 − t0, then each delta minus the previous delta]` (`[]` for no timestamps).
- `decode_timestamps(encoded)` reverses it.
- `timestamp_bits(ts)`: Gorilla's size in bits: 64 for the first timestamp, 14 for the first delta, and `dod_bits(d)` (done) for each delta of deltas after it.
- `downsample(points, step)` takes `(t, value)` points sorted by time and returns one `(bucket_start, min, max, mean, count)` per `step`-second bucket that has points, in order. Buckets start at multiples of `step`.

Experiment in the **Scratchpad**:

```python
from solution import ObjectStore, encode_timestamps, timestamp_bits

s = ObjectStore(chunk_size=4)
s.put("b", "a.txt", b"AAAABBBB")
s.put("b", "b.txt", b"BBBBAAAA")
print(len(s.chunks))  # deduplicated

ts = list(range(0, 15 * 1000, 15))
print(encode_timestamps(ts)[:5], timestamp_bits(ts) / len(ts), "bits per timestamp")
```

## Think about it

- Your store replaces an object by writing the new record, then releasing the old chunks. What could a concurrent reader see if you released first? What does that say about deleting chunks while reads are in flight?
- A photo service stores 2 billion photos averaging 200 KB. Compare the raw storage needed with 3× replication and with Reed-Solomon (10, 4). What does the cheaper option cost you when a disk dies?
- Why do TSDBs keep timestamps and values in separate columns instead of storing `(timestamp, value)` pairs together?

## Key terms

| Term | Meaning |
|---|---|
| Object store | Storage for immutable blobs addressed by bucket and key |
| Flat namespace | Keys with slashes in them, but no real directories |
| Common prefix | Keys rolled up at a delimiter in a listing, shown like a folder |
| ETag | A fingerprint of an object's content |
| Multipart upload | Uploading a large object as separately retried parts |
| Presigned URL | A time-limited signed URL for uploading or downloading one object |
| Content addressing | Naming data by a hash of its content |
| Erasure coding | k data shards plus m parity shards, any k of which rebuild the data |
| Reed-Solomon | The standard erasure code, built on polynomials over a finite field |
| Scrubbing | Re-reading stored data in the background to find corruption |
| Time series | Timestamped values for one metric and set of labels |
| Head block | A TSDB's in-memory block of the most recent data |
| Delta of deltas | The change between consecutive time gaps; 0 for regular samples |
| Gorilla compression | Delta-of-delta timestamps plus XOR-compressed values |
| Downsampling | Rolling raw points up into coarser buckets |
| Retention | How long each resolution of data is kept |
