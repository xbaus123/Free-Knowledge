"""A Bitcask-style key-value store: an append-only log plus an in-memory
hash index from each key to where its latest record starts."""

import os

import record


class KVStore:
    def __init__(self, path):
        self.path = path
        # key -> (offset, size) of the key's latest record in the log.
        self.index = {}
        if not os.path.exists(path):
            open(path, "wb").close()
        self.file = open(path, "r+b")
        self._load()

    def _load(self):
        """Rebuild the index by reading the log from the start.

        TODO: read records with record.read(self.file) until it returns
        None. Remember each key's offset and size; a tombstone (value None)
        removes the key. If you hit record.CorruptRecord, the rest of the
        file is a torn write: truncate the file there (self.file.truncate)
        so new records aren't appended after garbage.
        """

    def put(self, key, value):
        """TODO: append a record to the end of the log and index it."""

    def get(self, key):
        """TODO: return the key's latest value, or None.

        Use the index: seek to the offset and read exactly one record.
        """
        return None

    def delete(self, key):
        """TODO: append a tombstone and drop the key from the index."""

    def keys(self):
        return sorted(self.index)

    def close(self):
        self.file.close()
