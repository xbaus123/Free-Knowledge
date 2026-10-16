# Build a Key-Value Store: An Append-Only Log with a Hash Index

Time to build the simplest real storage engine from the last lesson: **Bitcask**, the design behind Riak's default backend. Every write is appended to a log file, and an in-memory **hash index** remembers where each key's latest record starts. Writes are sequential appends, and reads are one hash lookup plus one seek.

## The files

- **`record.py`** (read-only) defines the binary record format:

  ```text
  crc32 (4 bytes) | key length (4) | value length (4) | key | value
  ```

  ```python
  record.encode("user:1", "Ada")   # bytes for a record
  record.encode("user:1", None)    # bytes for a tombstone (a delete)
  record.read(f)                   # Record(key, value, size) at f's position, moving past it
                                   # None at end of file; raises record.CorruptRecord if torn
  ```

- **`kvstore.py`** is yours. `self.file` is the log, opened for reading and writing, and `self.index` maps each key to `(offset, size)` of its latest record.

## Your task

Implement `KVStore` in `kvstore.py`:

1. **`put(key, value)`**: append `record.encode(key, value)` to the **end** of the file (`self.file.seek(0, os.SEEK_END)`, then `tell()` gives the offset), flush, and update the index. Never overwrite old bytes: the log is append-only.
2. **`get(key)`**: look the key up in the index, seek to its offset, and read exactly **one** record. A key that isn't in the index needs no disk access at all.
3. **`delete(key)`**: append a **tombstone** and remove the key from the index. Deleting a key that doesn't exist does nothing.
4. **`_load()`**: the index lives in memory, so it's gone after a restart. Rebuild it by reading every record from the start of the file. Later records win, and a tombstone removes its key.
5. **Crash recovery**: if the process died halfway through an append, the file ends with a torn record and `record.read` raises `CorruptRecord`. Truncate the file at the start of that record (`self.file.truncate(offset)`) so new writes don't land after garbage.

Use the **Scratchpad** to experiment; your files are importable there:

```python
import os
from kvstore import KVStore

db = KVStore("demo.log")
for i in range(1000):
    db.put("counter", str(i))
print(db.get("counter"), os.path.getsize("demo.log"), "bytes for one key")
```

## Think about it

- Overwriting one key a million times makes the log a million records long, though only the last one matters. What would you do about that? (That's the next lesson: **segments and compaction**.)
- Every key must fit in memory. When would that be a problem?
- Why is appending faster than updating in place on both spinning disks and SSDs?
