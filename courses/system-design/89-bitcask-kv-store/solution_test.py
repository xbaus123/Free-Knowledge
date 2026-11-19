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


class KVStoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "data.log")
        self.db = KVStore(self.path)

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass
        shutil.rmtree(self.dir)

    def reopen(self):
        self.db.close()
        self.db = KVStore(self.path)

    def test_put_and_get(self):
        """stores values and returns the latest one for each key"""
        self.db.put("user:1", "Ada")
        self.db.put("user:2", "Grace")
        self.db.put("user:1", "Ada Lovelace")
        self.assertEqual(self.db.get("user:1"), "Ada Lovelace")
        self.assertEqual(self.db.get("user:2"), "Grace")
        self.assertIsNone(self.db.get("user:3"))
        self.db.put("emoji", "héllo wörld ✨")
        self.assertEqual(self.db.get("emoji"), "héllo wörld ✨")

    def test_delete(self):
        """deletes keys with a tombstone"""
        self.db.put("a", "1")
        self.db.put("b", "2")
        size = os.path.getsize(self.path)
        self.db.delete("a")
        self.assertIsNone(self.db.get("a"))
        self.assertEqual(self.db.keys(), ["b"])
        self.assertGreater(os.path.getsize(self.path), size, "a delete appends a tombstone record")
        self.db.delete("never-existed")  # no error

    def test_append_only(self):
        """never rewrites old records: updates are appended"""
        self.db.put("k", "first")
        with open(self.path, "rb") as f:
            before = f.read()
        self.db.put("k", "second")
        with open(self.path, "rb") as f:
            after = f.read()
        self.assertTrue(after.startswith(before), "the existing bytes of the log must not change")
        self.assertEqual(after[len(before):], record.encode("k", "second"))

    def test_index_points_at_records(self):
        """indexes each key by the offset and size of its latest record"""
        self.db.put("x", "1")
        self.db.put("y", "22")
        self.db.put("x", "333")
        self.assertEqual(set(self.db.index), {"x", "y"})
        for key, want in (("x", "333"), ("y", "22")):
            offset, size = self.db.index[key]
            self.assertEqual(size, len(record.encode(key, want)))
            with open(self.path, "rb") as f:
                f.seek(offset)
                rec = record.read(f)
            self.assertEqual((rec.key, rec.value), (key, want))

    def test_get_reads_one_record(self):
        """reads exactly one record per lookup instead of scanning the log"""
        for i in range(200):
            self.db.put(f"key{i % 50}", f"value{i}")
        with CountingReads() as reads:
            self.assertEqual(self.db.get("key7"), "value157")
        self.assertEqual(reads.calls, 1, "seek to the indexed offset and read a single record")
        with CountingReads() as reads:
            self.assertIsNone(self.db.get("missing"))
        self.assertEqual(reads.calls, 0, "a key that isn't in the index needs no disk read")

    def test_rebuilds_index_on_open(self):
        """recovers every key after a restart by replaying the log"""
        self.db.put("a", "1")
        self.db.put("b", "2")
        self.db.put("a", "3")
        self.db.delete("b")
        self.db.put("c", "4")
        self.reopen()
        self.assertEqual(self.db.get("a"), "3")
        self.assertIsNone(self.db.get("b"))
        self.assertEqual(self.db.keys(), ["a", "c"])

    def test_recovers_from_torn_write(self):
        """discards a half-written record left by a crash"""
        self.db.put("safe", "yes")
        self.db.close()
        with open(self.path, "ab") as f:
            f.write(record.encode("torn", "this write never finished")[:15])
        self.db = KVStore(self.path)
        self.assertEqual(self.db.get("safe"), "yes")
        self.assertIsNone(self.db.get("torn"))
        self.db.put("after", "crash")
        self.reopen()
        self.assertEqual(self.db.get("after"), "crash", "new records must not be appended after the torn bytes")
        with open(self.path, "rb") as f:
            records = []
            while (rec := record.read(f)) is not None:
                records.append(rec.key)
        self.assertEqual(records, ["safe", "after"])


if __name__ == "__main__":
    unittest.main()
