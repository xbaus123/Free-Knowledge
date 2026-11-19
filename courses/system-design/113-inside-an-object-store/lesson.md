# Inside an Object Store

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

## Inside an object store: metadata versus data

Every object store separates two very different jobs:

1. The **metadata service** maps `(bucket, key)` to an object record: size, ETag, version, user metadata, and the **list of chunks** that hold the data, with their locations. It's a partitioned, replicated key-value store. It's kept **sorted by key** so `LIST` with a prefix is a range scan, which makes it range-partitioned (chapter 6). Range partitioning has the usual hot-spot problem, which is why S3 documents per-prefix request rates (thousands of requests per second per prefix) and splits busy prefixes automatically.
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

Next, a short check on what you just read.
