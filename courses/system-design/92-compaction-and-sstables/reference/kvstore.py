"""A log-structured key-value store: log segments with a hash index, merged
by compaction into an SSTable with a sparse index."""

import bisect
import math
import os

import record
from layout import file_ids, segment_path, sstable_path


class KVStore:
    def __init__(self, directory, max_segment_bytes=1024, sparse_every=4):
        self.dir = directory
        self.max_segment_bytes = max_segment_bytes
        self.sparse_every = sparse_every
        os.makedirs(directory, exist_ok=True)
        # key -> (segment id, offset, size) of the key's latest record in a
        # log segment. The record may be a tombstone.
        self.index = {}
        # Log segment ids, oldest first. The last one is active (appended to).
        self.segments = []
        # The SSTable's id (None if there isn't one yet), and every
        # sparse_every-th key in it with its offset: [(key, offset), ...].
        self.sstable = None
        self.sparse_index = []
        self._readers = {}
        self._load()

    # --- opening ----------------------------------------------------------

    def _load(self):
        segments, sstables = file_ids(self.dir)
        if sstables:
            self.sstable = sstables[-1]
            self._load_sstable()
        for seg in segments:
            self._replay(seg)
        self.segments = segments
        if not segments:
            self.segments = [self._next_id()]
            open(segment_path(self.dir, self.segments[0]), "wb").close()
        self.active = open(segment_path(self.dir, self.segments[-1]), "r+b")

    def _replay(self, seg):
        """Index every record in a log segment; a torn tail is cut off."""
        path = segment_path(self.dir, seg)
        offset = 0
        with open(path, "r+b") as f:
            while True:
                try:
                    rec = record.read(f)
                except record.CorruptRecord:
                    f.truncate(offset)
                    break
                if rec is None:
                    break
                self.index[rec.key] = (seg, offset, rec.size)
                offset += rec.size

    def _scan(self, path):
        """Yields (offset, record) for every record in a file."""
        with open(path, "rb") as f:
            offset = 0
            while (rec := record.read(f)) is not None:
                yield offset, rec
                offset += rec.size

    def _load_sstable(self):
        """Builds the sparse index: every sparse_every-th key and its offset."""
        self.sparse_index = [
            (rec.key, offset)
            for i, (offset, rec) in enumerate(self._scan(sstable_path(self.dir, self.sstable)))
            if i % self.sparse_every == 0
        ]

    def _next_id(self):
        segments, sstables = file_ids(self.dir)
        return max(segments + sstables + self.segments + [0]) + 1

    # --- writing ----------------------------------------------------------

    def _append(self, key, value):
        self._roll_if_full()
        data = record.encode(key, value)
        self.active.seek(0, os.SEEK_END)
        offset = self.active.tell()
        self.active.write(data)
        self.active.flush()
        self.index[key] = (self.segments[-1], offset, len(data))

    def _roll_if_full(self):
        """Closes the active segment once it reaches max_segment_bytes and
        starts a new one."""
        self.active.seek(0, os.SEEK_END)
        if self.active.tell() < self.max_segment_bytes:
            return
        self.active.close()
        seg = self._next_id()
        self.segments.append(seg)
        self.active = open(segment_path(self.dir, seg), "w+b")

    def put(self, key, value):
        self._append(key, value)

    def delete(self, key):
        if self.get(key) is not None:
            self._append(key, None)

    # --- reading ----------------------------------------------------------

    def _reader(self, path):
        if path not in self._readers:
            self._readers[path] = open(path, "rb")
        return self._readers[path]

    def get(self, key):
        if key in self.index:
            seg, offset, _ = self.index[key]
            f = self._reader(segment_path(self.dir, seg))
            f.seek(offset)
            return record.read(f).value  # None for a tombstone
        return self._sstable_get(key)

    def _sstable_get(self, key):
        """Finds key in the SSTable: jump to the nearest sparse index entry
        at or before it, then scan at most sparse_every records."""
        if self.sstable is None:
            return None
        i = bisect.bisect_right(self.sparse_index, (key, math.inf)) - 1
        if i < 0:
            return None
        f = self._reader(sstable_path(self.dir, self.sstable))
        f.seek(self.sparse_index[i][1])
        for _ in range(self.sparse_every):
            rec = record.read(f)
            if rec is None or rec.key > key:
                return None
            if rec.key == key:
                return rec.value
        return None

    def keys(self):
        live = set()
        if self.sstable is not None:
            live.update(rec.key for _, rec in self._scan(sstable_path(self.dir, self.sstable)))
        live.update(self.index)
        return sorted(k for k in live if self.get(k) is not None)

    # --- compaction -------------------------------------------------------

    def compact(self):
        """Merges the SSTable and every closed segment into a new SSTable:
        sorted by key, latest value only, no tombstones."""
        closed = self.segments[:-1]
        if not closed:
            return
        latest = {}
        if self.sstable is not None:
            for _, rec in self._scan(sstable_path(self.dir, self.sstable)):
                latest[rec.key] = rec.value
        for seg in closed:  # oldest first, so newer records win
            for _, rec in self._scan(segment_path(self.dir, seg)):
                latest[rec.key] = rec.value

        new_id = self._next_id()
        path = sstable_path(self.dir, new_id)
        sparse = []
        with open(path + ".tmp", "wb") as f:
            for i, key in enumerate(sorted(k for k, v in latest.items() if v is not None)):
                if i % self.sparse_every == 0:
                    sparse.append((key, f.tell()))
                f.write(record.encode(key, latest[key]))
        os.replace(path + ".tmp", path)

        for f in self._readers.values():
            f.close()
        self._readers = {}
        old = [segment_path(self.dir, s) for s in closed]
        if self.sstable is not None:
            old.append(sstable_path(self.dir, self.sstable))
        for p in old:
            os.remove(p)
        self.sstable, self.sparse_index = new_id, sparse
        self.segments = self.segments[-1:]
        self.index = {k: loc for k, loc in self.index.items() if loc[0] == self.segments[0]}

    def close(self):
        self.active.close()
        for f in self._readers.values():
            f.close()
