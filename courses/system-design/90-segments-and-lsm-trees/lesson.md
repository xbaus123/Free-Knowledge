# Segments, SSTables, and LSM-Trees

*Chapter 3 · Data Models and Storage Engines.*

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

Next, a short check on what you just read.
