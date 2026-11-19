"""The on-disk record format. (Read-only: your store uses these helpers.)

Every record is a header followed by the key and value bytes:

    crc32 (4 bytes) | key length (4) | value length (4) | key | value

The checksum covers everything after it, so a record that was only half
written when the process crashed (a "torn write") is detected. A value
length of 0xFFFFFFFF marks a tombstone: the key was deleted.
"""

import struct
import zlib
from collections import namedtuple

HEADER_SIZE = 12
TOMBSTONE = 0xFFFFFFFF

Record = namedtuple("Record", "key value size")
"""key: str; value: str, or None for a tombstone; size: bytes on disk."""


class CorruptRecord(Exception):
    """The bytes at this position aren't a complete, valid record."""


def encode(key, value):
    """The bytes for a record. Pass value=None to encode a tombstone."""
    k = key.encode("utf-8")
    v = b"" if value is None else value.encode("utf-8")
    body = struct.pack(">II", len(k), TOMBSTONE if value is None else len(v)) + k + v
    return struct.pack(">I", zlib.crc32(body)) + body


def read(f):
    """Reads the record at the file's current position and moves past it.

    Returns a Record, or None at the end of the file. Raises CorruptRecord
    if the record is truncated or its checksum doesn't match.
    """
    header = f.read(HEADER_SIZE)
    if not header:
        return None
    if len(header) < HEADER_SIZE:
        raise CorruptRecord("truncated header")
    crc, klen, vlen = struct.unpack(">III", header)
    body_len = klen + (0 if vlen == TOMBSTONE else vlen)
    body = f.read(body_len)
    if len(body) < body_len:
        raise CorruptRecord("truncated record")
    if zlib.crc32(header[4:] + body) != crc:
        raise CorruptRecord("checksum mismatch")
    key = body[:klen].decode("utf-8")
    value = None if vlen == TOMBSTONE else body[klen:].decode("utf-8")
    return Record(key, value, HEADER_SIZE + body_len)
