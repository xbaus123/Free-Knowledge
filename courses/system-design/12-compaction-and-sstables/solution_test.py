import glob
import math
import os
import shutil
import tempfile
import unittest

import kvstore
import record
from kvstore import KVStore


class CountingReads:
    """Counts record.read calls, however kvstore imported it."""

    def __enter__(self):
        self.calls = 0
        self.original = record.read

        def counted(f):
            self.calls += 1
            return self.original(f)

        record.read = counted
        self.had_direct = hasattr(kvstore, "read")
        if self.had_direct:
            self.direct = kvstore.read
            kvstore.read = counted
        return self

    def __exit__(self, *exc):
        record.read = self.original
        if self.had_direct:
            kvstore.read = self.direct


def records(path):
    with open(path, "rb") as f:
        out = []
        while (rec := record.read(f)) is not None:
            out.append(rec)
        return out


class CompactionTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db = self.open()

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass
        shutil.rmtree(self.dir)

    def open(self):
        return KVStore(self.dir, max_segment_bytes=120, sparse_every=4)

    def reopen(self):
        self.db.close()
        self.db = self.open()

    def files(self, ext):
        return sorted(glob.glob(os.path.join(self.dir, "*." + ext)))

    def disk_bytes(self):
        return sum(os.path.getsize(p) for p in self.files("log") + self.files("sst"))

    def fill(self):
        """Writes 20 keys, overwrites each twice, and deletes a few."""
        want = {}
        for rnd in range(3):
            for i in range(20):
                key, value = f"user:{i:02d}", f"v{rnd}-{i}"
                self.db.put(key, value)
                want[key] = value
        for i in (3, 7, 11):
            self.db.delete(f"user:{i:02d}")
            del want[f"user:{i:02d}"]
        return want

    def check(self, want):
        for i in range(20):
            key = f"user:{i:02d}"
            self.assertEqual(self.db.get(key), want.get(key), key)
        self.assertEqual(self.db.keys(), sorted(want))

    def test_rolls_over_segments(self):
        """starts a new segment file when the active one is full"""
        want = self.fill()
        self.assertGreaterEqual(len(self.files("log")), 5, "with 120-byte segments, 63 records need many segment files")
        for path in self.files("log")[:-1]:
            self.assertGreaterEqual(os.path.getsize(path), 120, "only roll over once a segment reaches max_segment_bytes")
        self.check(want)
        self.reopen()
        self.check(want)

    def test_compaction_merges_closed_segments(self):
        """compacts closed segments into one SSTable and keeps the active one"""
        want = self.fill()
        before = self.disk_bytes()
        active = self.files("log")[-1]
        self.db.compact()
        self.assertEqual(len(self.files("sst")), 1, "compaction writes one SSTable")
        self.assertEqual(self.files("log"), [active], "closed segments are deleted; the active one stays")
        self.assertLess(self.disk_bytes(), before / 2, "overwritten values and deletes should be gone")
        self.check(want)

    def test_sstable_is_sorted_and_clean(self):
        """writes each live key once, sorted, without tombstones"""
        want = self.fill()
        self.db.compact()
        recs = records(self.files("sst")[0])
        keys = [r.key for r in recs]
        self.assertEqual(keys, sorted(set(keys)), "SSTable keys must be sorted and unique")
        self.assertTrue(all(r.value is not None for r in recs), "no tombstones in the SSTable")
        active_keys = {r.key for r in records(self.files("log")[0])}
        for r in recs:
            if r.key not in active_keys:
                self.assertEqual(r.value, want[r.key])

    def test_sparse_index(self):
        """keeps every 4th SSTable key in memory and scans at most 4 records"""
        for i in range(40):
            self.db.put(f"k{i:02d}", f"value-{i}")
        self.db.put("zz", "x" * 150)  # fills the segment, so the next put rolls over
        self.db.put("zzz", "active")
        self.db.compact()
        recs = records(self.files("sst")[0])
        offsets, offset = [], 0
        for r in recs:
            offsets.append((r.key, offset))
            offset += r.size
        self.assertEqual(self.db.sparse_index, offsets[::4])
        self.assertEqual(len(self.db.sparse_index), math.ceil(len(recs) / 4))
        self.assertLessEqual(len(self.db.index), 2, "after compaction the hash index holds only the active segment's keys")
        for key, want in (("k00", "value-0"), ("k17", "value-17"), ("k39", "value-39"), ("k171", None), ("a", None), ("k99", None)):
            with CountingReads() as reads:
                self.assertEqual(self.db.get(key), want, key)
            self.assertLessEqual(reads.calls, 4, f"get({key!r}) should read at most sparse_every records")

    def test_deletes_after_compaction(self):
        """a tombstone in the log hides a key in the SSTable, and the next compaction drops it"""
        want = self.fill()
        self.db.compact()
        old_sst = self.files("sst")
        self.db.delete("user:00")
        del want["user:00"]
        self.check(want)
        self.reopen()
        self.check(want)
        for i in range(20, 30):
            self.db.put(f"user:{i:02d}", "new")
            want[f"user:{i:02d}"] = "new"
        self.db.compact()
        self.assertEqual(len(self.files("sst")), 1)
        self.assertNotEqual(self.files("sst"), old_sst, "the merged SSTable replaces the old one")
        self.assertNotIn("user:00", [r.key for r in records(self.files("sst")[0])])
        for key, value in want.items():
            self.assertEqual(self.db.get(key), value, key)

    def test_reopen_after_compaction(self):
        """rebuilds the sparse index and hash index on restart"""
        want = self.fill()
        self.db.compact()
        sparse = list(self.db.sparse_index)
        self.reopen()
        self.assertEqual(self.db.sparse_index, sparse)
        self.check(want)

    def test_compacting_without_closed_segments(self):
        """does nothing when there is only the active segment"""
        self.db.put("a", "1")
        self.db.compact()
        self.assertEqual(self.files("sst"), [])
        self.assertEqual(self.db.get("a"), "1")


if __name__ == "__main__":
    unittest.main()
