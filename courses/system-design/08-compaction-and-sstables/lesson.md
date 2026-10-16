# Segments, Compaction, and SSTables

Your Bitcask store has two problems:

1. **The log grows forever.** Overwrite a key a million times and the file holds a million records, though only the last one matters.
2. **Every key lives in memory.** The hash index needs an entry for every key, however many there are.

Real log-structured engines fix both, and you'll do it in three steps, as in lesson 6:

- Split the log into **segments**. When the active segment is full, close it and start a new one. Closed segments never change.
- **Compact** closed segments. Merge them into one file holding only each key's latest value, with deleted keys dropped.
- Make the compacted file an **SSTable**, sorted by key. Because it's sorted, you don't need every key in memory: a **sparse index** of every 4th key is enough to find any record with a short scan.

## The layout

A store is now a directory:

```text
segment-000005.log   ← closed log segments (appended in order, never changed)
segment-000006.log   ← the active segment (new writes go here)
sstable-000004.sst   ← the compacted data, sorted by key
```

- **`record.py`** (read-only): the same record format as lesson 7.
- **`layout.py`** (read-only): `segment_path(dir, id)`, `sstable_path(dir, id)`, and `file_ids(dir)`.
- **`kvstore.py`**: yours. Opening, appending, replaying segments, and `get` for keys in the logs already work.

The state you'll use:

| Attribute | Meaning |
|---|---|
| `self.segments` | Segment ids, oldest first. The last one is active. |
| `self.active` | The open file of the active segment |
| `self.index` | key → `(segment id, offset, size)` of its latest log record. That record may be a tombstone. |
| `self.sstable` | The SSTable's id, or `None` |
| `self.sparse_index` | `[(key, offset), ...]` for SSTable records 0, 4, 8, … |
| `self._scan(path)` | Yields `(offset, record)` for every record in a file |

A lookup checks the hash index first, since the logs are newer than the SSTable. Only keys the logs don't mention go to the SSTable.

## Your task

Fill in the four TODOs in `kvstore.py`:

1. **`_roll_if_full()`**: once the active segment reaches `max_segment_bytes`, close it and start a new one with `self._next_id()`.
2. **`compact()`**: merge the old SSTable and the closed segments into a new SSTable.
   - Read the oldest first, so newer values win.
   - Drop tombstones. That's safe here, because every older copy of the key is in the files you're merging.
   - Write the live keys in **sorted order**, noting the offset of every `sparse_every`-th record.
   - Delete the merged files, and keep only the active segment's keys in `self.index`.
   - The active segment isn't touched, so writes can keep flowing while a real engine compacts in the background.
3. **`_load_sstable()`**: on startup, rebuild the sparse index by scanning the SSTable.
4. **`_sstable_get(key)`**: find the last sparse entry whose key is ≤ the one you want (`bisect` helps), seek to it, and read forward at most `sparse_every` records. Stop early once you pass the key, since the file is sorted.

The tests count disk reads: a lookup in the SSTable may read at most 4 records.

## Think about it

- This merge loads every key into a dictionary. Real engines merge SSTables like mergesort does: read them side by side and always write the smallest key next, so memory use stays constant. Why does sorting make that possible?
- Where would a **memtable** fit in? (Hint: sort writes in memory and flush them as SSTables directly.)
- What would a **Bloom filter** save when you look up a key that doesn't exist?
