"""Storage for big blobs and for metrics: a chunked object store, parity
for erasure coding, and a time-series compressor and downsampler."""

import hashlib


# --- 1. An object store ------------------------------------------------------


class NoSuchKey(Exception):
    pass


class ObjectStore:
    """Metadata (which chunks make up each object) is kept apart from the
    chunks themselves, which are stored once each, by content hash."""

    def __init__(self, chunk_size=4):
        self.chunk_size = chunk_size
        self.objects = {}  # (bucket, key) -> {"size", "etag", "chunks", "metadata"}
        self.chunks = {}  # SHA-256 hex digest -> bytes
        self.refs = {}  # SHA-256 hex digest -> how many object chunks use it
        self.chunk_reads = 0

    def put(self, bucket, key, data, metadata=None):
        """Store data under bucket/key, replacing any earlier version.
        Returns the ETag: the MD5 hex digest of data."""
        hashes = []
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i : i + self.chunk_size]
            digest = hashlib.sha256(chunk).hexdigest()
            if digest not in self.chunks:
                self.chunks[digest] = chunk
                self.refs[digest] = 0
            self.refs[digest] += 1
            hashes.append(digest)
        etag = hashlib.md5(data).hexdigest()
        old = self.objects.get((bucket, key))
        self.objects[(bucket, key)] = {
            "size": len(data),
            "etag": etag,
            "chunks": hashes,
            "metadata": dict(metadata or {}),
        }
        if old:
            self._release(old["chunks"])
        return etag

    def head(self, bucket, key):
        """An object's size, ETag, and metadata, without reading its data."""
        obj = self._object(bucket, key)
        return {"size": obj["size"], "etag": obj["etag"], "metadata": dict(obj["metadata"])}

    def get(self, bucket, key, start=0, end=None):
        """Bytes start up to (not including) end, reading only the chunks
        that hold them."""
        obj = self._object(bucket, key)
        end = obj["size"] if end is None else min(end, obj["size"])
        if start >= end:
            return b""
        first, last = start // self.chunk_size, (end - 1) // self.chunk_size
        data = b"".join(self._read(h) for h in obj["chunks"][first : last + 1])
        offset = first * self.chunk_size
        return data[start - offset : end - offset]

    def delete(self, bucket, key):
        obj = self.objects.pop((bucket, key), None)
        if obj:
            self._release(obj["chunks"])

    def list(self, bucket, prefix="", delimiter=None):
        """(keys, common prefixes) in the bucket that start with prefix, both
        sorted. With a delimiter, keys with another delimiter after the prefix
        are rolled up into one common prefix each, like folders."""
        keys = sorted(k for b, k in self.objects if b == bucket and k.startswith(prefix))
        if not delimiter:
            return keys, []
        contents, prefixes = [], set()
        for k in keys:
            i = k.find(delimiter, len(prefix))
            if i < 0:
                contents.append(k)
            else:
                prefixes.add(k[: i + len(delimiter)])
        return contents, sorted(prefixes)

    def _object(self, bucket, key):
        try:
            return self.objects[(bucket, key)]
        except KeyError:
            raise NoSuchKey(f"{bucket}/{key}") from None

    def _read(self, digest):
        self.chunk_reads += 1
        return self.chunks[digest]

    def _release(self, hashes):
        for digest in hashes:
            self.refs[digest] -= 1
            if self.refs[digest] == 0:
                del self.refs[digest]
                del self.chunks[digest]


# --- 2. Erasure coding -------------------------------------------------------


def split(data, k):
    """Cut data into k equal shards, padding the last with zero bytes."""
    size = -(-len(data) // k) if data else 1
    data = data.ljust(size * k, b"\0")
    return [data[i * size : (i + 1) * size] for i in range(k)]


def parity(shards):
    """The XOR of equal-length shards, byte by byte."""
    out = bytearray(len(shards[0]))
    for shard in shards:
        for i, b in enumerate(shard):
            out[i] ^= b
    return bytes(out)


def recover(shards, parity_shard):
    """Rebuild the one shard that is None from the others and the parity."""
    missing = [i for i, s in enumerate(shards) if s is None]
    if len(missing) != 1:
        raise ValueError("parity can rebuild exactly one lost shard")
    rebuilt = parity([s for s in shards if s is not None] + [parity_shard])
    return shards[: missing[0]] + [rebuilt] + shards[missing[0] + 1 :]


# --- 3. Time series ----------------------------------------------------------


def encode_timestamps(timestamps):
    """[t0, t1 - t0, then each delta minus the previous delta]."""
    if not timestamps:
        return []
    out = [timestamps[0]]
    prev_delta = None
    for a, b in zip(timestamps, timestamps[1:]):
        delta = b - a
        out.append(delta if prev_delta is None else delta - prev_delta)
        prev_delta = delta
    return out


def decode_timestamps(encoded):
    """The inverse of encode_timestamps."""
    if not encoded:
        return []
    out = [encoded[0]]
    delta = 0
    for i, value in enumerate(encoded[1:]):
        delta = value if i == 0 else delta + value
        out.append(out[-1] + delta)
    return out


def dod_bits(dod):
    """Gorilla's variable-length code for one delta of deltas."""
    if dod == 0:
        return 1
    if -63 <= dod <= 64:
        return 2 + 7
    if -255 <= dod <= 256:
        return 3 + 9
    if -2047 <= dod <= 2048:
        return 4 + 12
    return 4 + 32


def timestamp_bits(timestamps):
    """Bits to store timestamps Gorilla-style: 64 for the first, 14 for the
    first delta, then dod_bits for each delta of deltas."""
    encoded = encode_timestamps(timestamps)
    if not encoded:
        return 0
    bits = 64
    if len(encoded) > 1:
        bits += 14 + sum(dod_bits(d) for d in encoded[2:])
    return bits


def downsample(points, step):
    """[(t, value)] sorted by t -> [(bucket start, min, max, mean, count)],
    one per step-second bucket that has points."""
    out = []
    for t, v in points:
        start = t - t % step
        if out and out[-1][0] == start:
            s, lo, hi, total, n = out[-1]
            out[-1] = (s, min(lo, v), max(hi, v), total + v, n + 1)
        else:
            out.append((start, v, v, v, 1))
    return [(s, lo, hi, total / n, n) for s, lo, hi, total, n in out]
