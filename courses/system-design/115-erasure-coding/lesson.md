# Durability: Replication vs. Erasure Coding

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

## Durability: replication versus erasure coding

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

## Object stores in system design

- **Uploads**: the client asks your API for a presigned URL and uploads directly to the store. The API servers never touch the bytes.
- **Delivery**: put a CDN (chapter 6) in front. Immutable objects with versioned keys cache perfectly.
- **Data lakes**: analytical data lives as columnar Parquet files (chapter 3) in object storage, with table formats like Apache Iceberg and Delta Lake adding transactions on top. Batch jobs (chapter 9) read immutable inputs and write new outputs.
- **Cheap durable backing for other systems**: Kafka tiered storage, database backups, and long-term metrics (below) all offload old data to object storage.

Next, a short check on what you just read.
