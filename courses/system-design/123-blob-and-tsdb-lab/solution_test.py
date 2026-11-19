import hashlib
import random
import unittest

from solution import (
    NoSuchKey,
    ObjectStore,
    decode_timestamps,
    downsample,
    encode_timestamps,
    parity,
    recover,
    split,
    timestamp_bits,
)


class ObjectStoreTest(unittest.TestCase):
    def test_round_trip(self):
        """stores and returns objects with their metadata"""
        s = ObjectStore(chunk_size=4)
        etag = s.put("photos", "cat.jpg", b"meow meow meow", {"content-type": "image/jpeg"})
        self.assertEqual(etag, hashlib.md5(b"meow meow meow").hexdigest())
        self.assertEqual(s.get("photos", "cat.jpg"), b"meow meow meow")
        self.assertEqual(
            s.head("photos", "cat.jpg"),
            {"size": 14, "etag": etag, "metadata": {"content-type": "image/jpeg"}},
        )
        self.assertEqual(s.objects[("photos", "cat.jpg")]["chunks"], [hashlib.sha256(c).hexdigest() for c in [b"meow", b" meo", b"w me", b"ow"]])

    def test_head_reads_no_data(self):
        """answers head from metadata alone"""
        s = ObjectStore()
        s.put("b", "k", b"x" * 100)
        s.chunk_reads = 0
        s.head("b", "k")
        self.assertEqual(s.chunk_reads, 0)

    def test_missing(self):
        """raises NoSuchKey for objects that don't exist"""
        s = ObjectStore()
        s.put("b", "k", b"data")
        with self.assertRaises(NoSuchKey):
            s.get("b", "nope")
        with self.assertRaises(NoSuchKey):
            s.get("other-bucket", "k")
        with self.assertRaises(NoSuchKey):
            s.head("b", "nope")
        s.delete("b", "nope")  # deleting what isn't there succeeds, as in S3

    def test_empty_object(self):
        """stores an empty object"""
        s = ObjectStore()
        s.put("b", "empty", b"")
        self.assertEqual(s.get("b", "empty"), b"")
        self.assertEqual(s.head("b", "empty")["size"], 0)

    def test_ranges(self):
        """reads byte ranges"""
        s = ObjectStore(chunk_size=4)
        data = b"0123456789abcdef"
        s.put("b", "k", data)
        for start, end in [(0, 16), (0, 4), (3, 9), (8, 12), (15, 16), (10, None), (5, 100), (7, 7), (20, 30)]:
            self.assertEqual(s.get("b", "k", start, end), data[start:end], (start, end))

    def test_ranges_read_few_chunks(self):
        """reads only the chunks a range touches"""
        s = ObjectStore(chunk_size=4)
        s.put("b", "video.mp4", bytes(range(256)) * 4)
        s.chunk_reads = 0
        s.get("b", "video.mp4", 10, 14)
        self.assertEqual(s.chunk_reads, 2, "bytes 10-13 span chunks 2 and 3")
        s.chunk_reads = 0
        s.get("b", "video.mp4", 512, 516)
        self.assertEqual(s.chunk_reads, 1)

    def test_dedup(self):
        """stores identical chunks once"""
        s = ObjectStore(chunk_size=4)
        s.put("b", "one", b"AAAABBBBAAAA")
        s.put("b", "two", b"BBBBAAAA")
        self.assertEqual(len(s.chunks), 2)
        self.assertEqual(s.get("b", "two"), b"BBBBAAAA")

    def test_delete_frees_unshared_chunks(self):
        """deletes chunks once no object uses them"""
        s = ObjectStore(chunk_size=4)
        s.put("b", "one", b"AAAABBBB")
        s.put("b", "two", b"BBBBCCCC")
        s.delete("b", "one")
        self.assertEqual(sorted(s.chunks.values()), [b"BBBB", b"CCCC"])
        self.assertEqual(s.get("b", "two"), b"BBBBCCCC")
        s.delete("b", "two")
        self.assertEqual(s.chunks, {})
        with self.assertRaises(NoSuchKey):
            s.get("b", "two")

    def test_overwrite(self):
        """replaces an object and frees the old version's chunks"""
        s = ObjectStore(chunk_size=4)
        s.put("b", "k", b"old!old!", {"v": "1"})
        s.put("b", "k", b"new!", {"v": "2"})
        self.assertEqual(s.get("b", "k"), b"new!")
        self.assertEqual(s.head("b", "k")["metadata"], {"v": "2"})
        self.assertEqual(list(s.chunks.values()), [b"new!"])
        s.put("b", "k", b"new!")  # the same content again
        self.assertEqual(list(s.chunks.values()), [b"new!"], "the chunk survives being replaced by itself")
        self.assertEqual(s.get("b", "k"), b"new!")

    def test_list(self):
        """lists keys by prefix"""
        s = ObjectStore()
        for key in ["logs/2026/10/01.gz", "logs/2026/10/02.gz", "logs/2026/11/01.gz", "logs/readme.txt", "index.html"]:
            s.put("site", key, b"x")
        s.put("other", "logs/secret", b"x")
        self.assertEqual(s.list("site"), (["index.html", "logs/2026/10/01.gz", "logs/2026/10/02.gz", "logs/2026/11/01.gz", "logs/readme.txt"], []))
        self.assertEqual(s.list("site", "logs/2026/10/")[0], ["logs/2026/10/01.gz", "logs/2026/10/02.gz"])
        self.assertEqual(s.list("empty"), ([], []))

    def test_list_delimiter(self):
        """rolls keys up into common prefixes, like folders"""
        s = ObjectStore()
        for key in ["logs/2026/10/01.gz", "logs/2026/10/02.gz", "logs/2026/11/01.gz", "logs/readme.txt", "index.html"]:
            s.put("site", key, b"x")
        self.assertEqual(s.list("site", delimiter="/"), (["index.html"], ["logs/"]))
        self.assertEqual(s.list("site", "logs/", "/"), (["logs/readme.txt"], ["logs/2026/"]))
        self.assertEqual(s.list("site", "logs/2026/", "/"), ([], ["logs/2026/10/", "logs/2026/11/"]))
        self.assertEqual(s.list("site", "logs/20", "/"), ([], ["logs/2026/"]), "a prefix needn't end at a slash")


class ErasureCodingTest(unittest.TestCase):
    def test_parity(self):
        """XORs shards byte by byte"""
        self.assertEqual(parity([b"\x0f\xf0", b"\xff\x00"]), b"\xf0\xf0")
        self.assertEqual(parity([b"abc"]), b"abc")
        self.assertEqual(parity([b"abc", b"abc"]), b"\0\0\0")

    def test_recover_any_shard(self):
        """rebuilds any one lost shard"""
        shards = split(b"The quick brown fox jumps over the lazy dog", 4)
        p = parity(shards)
        for lost in range(4):
            damaged = shards[:lost] + [None] + shards[lost + 1 :]
            self.assertEqual(recover(damaged, p), shards, f"lost shard {lost}")

    def test_round_trip(self):
        """stores data as k shards plus parity and gets it back after a loss"""
        rng = random.Random(1)
        for k in [2, 3, 6, 10]:
            data = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 300)))
            shards = split(data, k)
            p = parity(shards)
            shards[rng.randrange(k)] = None
            self.assertEqual(b"".join(recover(shards, p))[: len(data)], data)

    def test_too_many_losses(self):
        """refuses when more than one shard is lost"""
        shards = split(b"abcdefgh", 4)
        p = parity(shards)
        with self.assertRaises(ValueError):
            recover([None, None] + shards[2:], p)
        with self.assertRaises(ValueError):
            recover(shards, p)


class TimeSeriesTest(unittest.TestCase):
    def test_encode(self):
        """stores the first timestamp, the first delta, then deltas of deltas"""
        self.assertEqual(encode_timestamps([1000, 1060, 1120, 1180, 1241, 1300]), [1000, 60, 0, 0, 1, -2])
        self.assertEqual(encode_timestamps([5]), [5])
        self.assertEqual(encode_timestamps([]), [])
        self.assertEqual(encode_timestamps([10, 20]), [10, 10])

    def test_decode(self):
        """decodes back to the original timestamps"""
        self.assertEqual(decode_timestamps([1000, 60, 0, 0, 1, -2]), [1000, 1060, 1120, 1180, 1241, 1300])
        self.assertEqual(decode_timestamps([]), [])
        rng = random.Random(4)
        ts, t = [], 1_700_000_000
        for _ in range(500):
            t += rng.choice([15, 15, 15, 14, 16, 30, 1])
            ts.append(t)
        self.assertEqual(decode_timestamps(encode_timestamps(ts)), ts)

    def test_bits(self):
        """counts Gorilla's bits"""
        self.assertEqual(timestamp_bits([]), 0)
        self.assertEqual(timestamp_bits([1000]), 64)
        self.assertEqual(timestamp_bits([1000, 1060]), 64 + 14)
        self.assertEqual(timestamp_bits([1000, 1060, 1120, 1180, 1241, 1300]), 64 + 14 + 1 + 1 + 9 + 9)
        self.assertEqual(timestamp_bits([0, 10, 20, 130, 1240, 12350]), 64 + 14 + 1 + 12 + 16 + 36)

    def test_regular_series_compress(self):
        """stores a steady scrape in about 1 bit per point"""
        ts = list(range(1_700_000_000, 1_700_000_000 + 15 * 2000, 15))
        self.assertEqual(timestamp_bits(ts), 64 + 14 + 1998)
        self.assertLess(timestamp_bits(ts) / len(ts), 1.1, "versus 64 bits for a raw timestamp")

    def test_downsample(self):
        """rolls points up into buckets with min, max, mean, and count"""
        points = [(0, 5.0), (15, 7.0), (30, 3.0), (45, 9.0), (60, 4.0), (75, 4.0), (185, 10.0)]
        self.assertEqual(
            downsample(points, 60),
            [(0, 3.0, 9.0, 6.0, 4), (60, 4.0, 4.0, 4.0, 2), (180, 10.0, 10.0, 10.0, 1)],
        )
        self.assertEqual(downsample([], 60), [])

    def test_downsample_offsets(self):
        """aligns buckets to multiples of the step"""
        self.assertEqual(downsample([(119, 1.0), (120, 2.0), (3599, 3.0)], 3600), [(0, 1.0, 3.0, 2.0, 3)])
        self.assertEqual([b[0] for b in downsample([(59, 1), (61, 1), (300, 1)], 60)], [0, 60, 300])


if __name__ == "__main__":
    unittest.main()
