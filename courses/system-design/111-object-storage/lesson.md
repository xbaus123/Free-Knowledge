# Object Storage and the Object Model

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

*Based on* Designing Data-Intensive Applications*, Chapters 3 and 10.*

*Based on* Designing Data-Intensive Applications*, Chapters 3 and 10.*

The storage engines you've built so far store **records**: keys and values of a few bytes to a few kilobytes, read and updated at random. Two workloads break that shape completely:

- **Blobs**: photos, videos, backups, log archives, machine-learning datasets. Megabytes to terabytes each, written once, read whole or in ranges, almost never modified.
- **Time series**: metrics, sensor readings, stock ticks. Billions of tiny `(timestamp, value)` points, arriving in time order, never updated, queried in time ranges, and worth less the older they get.

Each gets its own kind of storage system, and each takes ideas you've already met (immutable files, content hashing, column storage, compaction) to an extreme. The next readings cover both: **object stores** like Amazon S3, and **time-series databases (TSDBs)** like Prometheus.

## Why not the database, or a filesystem?

You *can* put a 20 MB video in a database column. It's a bad idea. Every copy of the database now carries it: the buffer pool caches it at the expense of hot rows, the replication log ships it to every follower (chapter 5), every backup copies it, and every migration rewrites it. Databases also cap value sizes and aren't built to stream gigabytes. The standard pattern is to keep the **blob** in an object store and the **pointer** (its key) plus searchable metadata in the database.

A distributed filesystem with POSIX semantics (directories, renames, locks, in-place overwrites, appends) is expensive to scale, because every one of those operations needs coordination across machines. Object stores get their scale by **giving most of that up**.

## The object model

- A **bucket** is a namespace, and an **object** is a key, some bytes, and metadata (content type, custom headers).
- The namespace is **flat**. `logs/2026/10/01.gz` is just a key that happens to contain slashes. "Folders" are an illusion created by **listing** with a prefix and a **delimiter**: list `logs/` with delimiter `/`, and the store rolls up every key with another slash after the prefix into one **common prefix**, `logs/2026/`. Renaming a "folder" means copying every object under it.
- Objects are **immutable**: a `PUT` writes the whole object at once. There's no partial update and no append. Writing the same key again replaces the object atomically, so readers see the old version or the new one, never a mix.
- `GET` can read a **byte range**, which is how video players seek and download tools fetch pieces in parallel. `HEAD` returns the metadata without the data.
- Each object has an **ETag**, a fingerprint of its content (for simple uploads, the MD5 of its bytes), so clients can check integrity and make conditional requests ("only if it changed").

On top of that, object stores add **versioning** (keep every version of a key), **lifecycle rules** (move objects to cheaper storage classes after 30 days, delete after a year), **storage classes** trading retrieval latency for price (from milliseconds to hours, for archival tiers), and **presigned URLs**: a URL signed with a key that lets a client upload or download one object directly for a limited time, without its traffic passing through your servers or your servers holding its credentials (chapter 2).

S3 has offered strong read-after-write consistency since December 2020. Before that, overwrites and listings were only eventually consistent, and a `GET` right after an overwrite could return the old object, a lagging-replica problem at planetary scale.

Next, a short check on what you just read.
