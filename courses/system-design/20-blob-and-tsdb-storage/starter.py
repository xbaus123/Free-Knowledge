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
        raise NotImplementedError

    def head(self, bucket, key):
        """An object's size, ETag, and metadata, without reading its data."""
        raise NotImplementedError

    def get(self, bucket, key, start=0, end=None):
        """Bytes start up to (not including) end, reading only the chunks
        that hold them."""
        raise NotImplementedError

    def delete(self, bucket, key):
        raise NotImplementedError

    def list(self, bucket, prefix="", delimiter=None):
        """(keys, common prefixes) in the bucket that start with prefix, both
        sorted. With a delimiter, keys with another delimiter after the prefix
        are rolled up into one common prefix each, like folders."""
        raise NotImplementedError

    def _object(self, bucket, key):
        try:
            return self.objects[(bucket, key)]
        except KeyError:
            raise NoSuchKey(f"{bucket}/{key}") from None

    def _read(self, digest):
        self.chunk_reads += 1
        return self.chunks[digest]

    def _release(self, hashes):
        """Drop one reference to each chunk, deleting chunks nobody uses."""
        raise NotImplementedError


# --- 2. Erasure coding -------------------------------------------------------


def split(data, k):
    """Cut data into k equal shards, padding the last with zero bytes."""
    size = -(-len(data) // k) if data else 1
    data = data.ljust(size * k, b"\0")
    return [data[i * size : (i + 1) * size] for i in range(k)]


def parity(shards):
    """The XOR of equal-length shards, byte by byte."""
    raise NotImplementedError


def recover(shards, parity_shard):
    """Rebuild the one shard that is None from the others and the parity."""
    raise NotImplementedError


# --- 3. Time series ----------------------------------------------------------


def encode_timestamps(timestamps):
    """[t0, t1 - t0, then each delta minus the previous delta]."""
    raise NotImplementedError


def decode_timestamps(encoded):
    """The inverse of encode_timestamps."""
    raise NotImplementedError


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
    raise NotImplementedError


def downsample(points, step):
    """[(t, value)] sorted by t -> [(bucket start, min, max, mean, count)],
    one per step-second bucket that has points."""
    raise NotImplementedError
