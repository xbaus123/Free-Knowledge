# Storage Engines: Logs, LSM-Trees, and B-Trees

*Based on* Designing Data-Intensive Applications*, Chapter 3.*

A database does two things: store data you give it, and give it back when you ask. How it lays that data out on disk decides how fast writes and reads are. You don't need to write a database to use one well, but knowing what's inside tells you which one fits your workload. In the next two lessons, you'll build one.

## The simplest database: an append-only log

```bash
db_set() { echo "$1,$2" >> database; }
db_get() { grep "^$1," database | sed -e "s/^$1,//" | tail -n 1; }
```

Writes are about as fast as they can be: **appending** to the end of a file is sequential I/O. Updating a key appends a new line, and the latest one wins. Reads are terrible: `db_get` scans the whole file, which is O(n).

The **log** (an append-only sequence of records) is the core of many real databases. To read efficiently, you add an **index**: extra data that tells you where to look. Every index speeds up some reads and slows down every write, which is why databases don't index everything by default.

## Hash indexes (Bitcask)

Keep an in-memory **hash map** from each key to the **byte offset** of its latest record in the log. A read is one hash lookup plus one disk seek. This is how **Bitcask** (Riak's default engine) works. It's ideal when there are many writes per key but all the keys fit in memory.

Details that make it real:

- **Record format**: a binary header (checksum, key length, value length) followed by the bytes. Binary is faster and more compact than CSV, and needs no escaping.
- **Deletes** append a special **tombstone** record. Readers treat it as "this key is gone."
- **Crash recovery**: the hash map lives in memory and is lost on restart, so rebuild it by reading the log from start to end.
- **Partially written records**: a crash mid-append leaves a torn record at the end of the file. A **checksum** detects it, and recovery discards it.
- **Concurrency**: a single writer appends, and many readers can read the immutable data at once.

## Segments and compaction

An append-only log grows forever. So break it into **segments**: when the active file reaches a size limit, close it and start a new one. Closed segments are immutable, so a background thread can **compact** them: throw away overwritten values and tombstoned keys, and keep only the latest value for each key. Merging several compacted segments shrinks the data further. Reads check the newest segment's index first, then older ones.

## SSTables and LSM-trees

Now require each segment to be **sorted by key**. That's a **Sorted String Table (SSTable)**, and it brings big advantages:

1. **Merging is efficient**, like the merge step of mergesort: read the input segments side by side and write the smallest key first. When the same key appears in several segments, keep the newest.
2. **The index can be sparse.** You don't need every key in memory, just one key every few kilobytes. To find `handiwork`, if you know the offsets of `handbag` and `handsome`, scan from `handbag`'s offset.
3. **Blocks can be compressed** between index entries, saving disk space and I/O.

But writes arrive in any order. How do you produce sorted files? Buffer them in memory:

1. A write goes into an in-memory balanced tree, the **memtable**, and is appended to a write-ahead log for crash safety.
2. When the memtable gets big, write it out as a new SSTable segment. It's already sorted.
3. Reads check the memtable, then the newest SSTable, then older ones.
4. In the background, **compaction** merges SSTables and discards stale values.

This design is the **Log-Structured Merge-Tree (LSM-tree)**, used by LevelDB, RocksDB, Cassandra, HBase, and many more. Two refinements:

- **Bloom filters** answer "is this key definitely *not* in this segment?" cheaply, so lookups for missing keys don't read every segment.
- **Compaction strategies**: *size-tiered* merges similar-sized SSTables (Cassandra's default). *Leveled* keeps fixed-size SSTables in levels of increasing size (LevelDB, RocksDB).

## B-trees

The most widely used index structure, and the default in almost every relational database. B-trees also keep keys sorted, but organize them very differently:

- The data is divided into fixed-size **pages** (typically 4 KB), and pages refer to other pages, forming a tree.
- The root page holds keys and references to child pages, each covering a range of keys. Following references down leads to a **leaf page** holding the value (or a pointer to it).
- The **branching factor** is several hundred children per page, so the tree stays shallow. A four-level tree of 4 KB pages with a branching factor of 500 can store 256 TB.
- Updates **overwrite pages in place**. If a page overflows, it splits in two and the parent is updated.

Overwriting in place is risky: a crash in the middle of a page split could corrupt the tree. So B-trees write every change to a **write-ahead log (WAL)** first, and replay it after a crash. Concurrent access needs **latches** (lightweight locks) on pages.

## Comparing them

| | LSM-tree | B-tree |
|---|---|---|
| Writes | Sequential appends and merges: usually faster | Random page overwrites, plus the WAL |
| Reads | May check several structures: usually slower | One path from root to leaf: predictable |
| Disk space | Compacts well, less fragmentation | Pages partly empty after splits |
| Each key lives in | Possibly several segments until compaction | Exactly one place, which suits transactions and locks |
| Background cost | Compaction can compete with live traffic | Little |

**Write amplification** is the number of bytes written to disk for each byte the application writes. Both designs rewrite data more than once: B-trees through the WAL and whole-page writes, LSM-trees through repeated compaction. On write-heavy workloads, it's often the bottleneck. SSDs also wear out with writes. LSM-trees usually have lower write amplification, but their throughput can suffer when compaction can't keep up with incoming writes.

## OLTP vs. OLAP

Storage engines also split by **access pattern**:

| | OLTP (transaction processing) | OLAP (analytics) |
|---|---|---|
| Typical query | Fetch a few records by key | Aggregate over millions of rows |
| Writes | Random-access, low-latency writes from users | Bulk import (ETL) or event streams |
| Used by | End users, through the application | Analysts and dashboards |
| Data | The current state | The history of events |
| Size | Gigabytes to terabytes | Terabytes to petabytes |

Analytics workloads moved to separate **data warehouses**, loaded through **ETL** (extract, transform, load) so they can't slow down the production database. Warehouses often use a **star schema**: a large **fact table** of events (each sale) surrounded by **dimension tables** (product, store, date).

Warehouses also store data in **columns** instead of rows. A query that reads 3 columns of a 100-column table only touches those 3 files. Each column holds similar values, so it compresses extremely well (bitmaps, run-length encoding). Parquet, BigQuery, Snowflake, Redshift, and ClickHouse all work this way.

## Key terms

| Term | Meaning |
|---|---|
| Log | An append-only sequence of records |
| Tombstone | A record marking a key as deleted |
| Segment | One file of the log; closed segments are immutable |
| Compaction | Rewriting segments to drop overwritten and deleted values |
| SSTable | A segment sorted by key, with a sparse index |
| Memtable | The in-memory sorted buffer of recent writes |
| LSM-tree | Memtable + SSTables + background compaction |
| B-tree | A tree of fixed-size pages, updated in place, with a WAL |
| Write amplification | Bytes written to disk per byte the application writes |
