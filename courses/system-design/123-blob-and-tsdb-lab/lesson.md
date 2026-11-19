# Blob and Time-Series Storage: Object Stores, Erasure Coding, and TSDBs

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

Build what the last six readings described: a chunked, deduplicating object store with ranged reads and prefix listing, XOR parity, and Gorilla timestamps with downsampling.

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
