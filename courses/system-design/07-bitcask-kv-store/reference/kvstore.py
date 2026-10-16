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
        """Rebuild the index by reading the log from the start."""
        self.file.seek(0)
        offset = 0
        while True:
            try:
                rec = record.read(self.file)
            except record.CorruptRecord:
                # A torn write from a crash: drop it.
                self.file.truncate(offset)
                break
            if rec is None:
                break
            if rec.value is None:
                self.index.pop(rec.key, None)
            else:
                self.index[rec.key] = (offset, rec.size)
            offset += rec.size

    def _append(self, data):
        self.file.seek(0, os.SEEK_END)
        offset = self.file.tell()
        self.file.write(data)
        self.file.flush()
        return offset

    def put(self, key, value):
        data = record.encode(key, value)
        self.index[key] = (self._append(data), len(data))

    def get(self, key):
        if key not in self.index:
            return None
        offset, _ = self.index[key]
        self.file.seek(offset)
        return record.read(self.file).value

    def delete(self, key):
        if key in self.index:
            self._append(record.encode(key, None))
            del self.index[key]

    def keys(self):
        return sorted(self.index)

    def close(self):
        self.file.close()
