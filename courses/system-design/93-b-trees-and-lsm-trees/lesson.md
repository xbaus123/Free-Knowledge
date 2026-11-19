# B-Trees, and How They Compare

*Chapter 3 · Data Models and Storage Engines.*

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

Next, a short check on what you just read.
