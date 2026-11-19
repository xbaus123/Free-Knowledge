# Logs and Hash Indexes

*Chapter 3 · Data Models and Storage Engines.*

*Based on* Designing Data-Intensive Applications*, Chapter 3.*

*Based on* Designing Data-Intensive Applications*, Chapter 3.*

A database does two things: store data you give it, and give it back when you ask. How it lays that data out on disk decides how fast writes and reads are. You don't need to write a database to use one well, but knowing what's inside tells you which one fits your workload. In the two labs in this chapter, you'll build one.

## The simplest database: an append-only log

```bash
db_set() { echo "$1,$2" >> database; }
db_get() { grep "^$1," database | sed -e "s/^$1,//" | tail -n 1; }
```

Writes are about as fast as they can be: **appending** to the end of a file is sequential I/O. Updating a key appends a new line, and the latest one wins. Reads are terrible: `db_get` scans the whole file, which is O(n).

The **log** (an append-only sequence of records) is the core of many real databases. To read efficiently, you add an **index**: extra data that tells you where to look. Every index speeds up some reads and slows down every write, which is why databases don't index everything by default.

## Hash indexes (Bitcask)

Keep an in-memory **hash map** from each key to the **byte offset** of its latest record in the log. A read is one hash lookup plus one disk seek. This is how **Bitcask** (Riak's default engine) works. It's ideal when there are many writes per key but all the keys fit in memory.

Details that make it real:

- **Record format**: a binary header (checksum, key length, value length) followed by the bytes. Binary is faster and more compact than CSV, and needs no escaping.
- **Deletes** append a special **tombstone** record. Readers treat it as "this key is gone."
- **Crash recovery**: the hash map lives in memory and is lost on restart, so rebuild it by reading the log from start to end.
- **Partially written records**: a crash mid-append leaves a torn record at the end of the file. A **checksum** detects it, and recovery discards it.
- **Concurrency**: a single writer appends, and many readers can read the immutable data at once.

Next, a short check on what you just read.
