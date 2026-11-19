# Partitioning by Key Range and by Hash

*Chapter 6 · Partitioning and Geography.*

*Based on* Designing Data-Intensive Applications*, Chapter 6.*

*Based on* Designing Data-Intensive Applications*, Chapter 6.*

Replication puts the *same* data on several machines. When the data, or the write load, is too big for one machine, you also need **partitioning**: splitting the data so each machine holds a different subset. Partitions are called **shards** in MongoDB and Elasticsearch, **regions** in HBase, **tablets** in Bigtable, and **vnodes** in Cassandra and Riak. The two are usually combined: each partition is replicated to several nodes, and each node holds several partitions.

The goal is to spread data and queries **evenly**. If some partitions get more than their share, partitioning is **skewed**, and an overloaded partition is a **hot spot**.

## Partitioning by key range

Give each partition a continuous range of keys, like the volumes of an encyclopedia: A–Ce, Cf–F, and so on. The boundaries don't have to be even; they adapt to the data.

- ✓ Keys within a partition stay **sorted**, so **range scans** are efficient ("all readings from sensor 42 in March").
- ✗ Some access patterns create hot spots. With timestamp keys, all of today's writes land on one partition. A common fix is to prefix the key with something else, such as the sensor name, so writes spread out at the cost of range queries over time.

HBase, Bigtable, and MongoDB (in range mode) work this way.

## Partitioning by hash of key

Hash each key and give each partition a range of **hashes**. A good hash function (MD5 or Murmur3, *not* a language's built-in `hash()`, which may differ between processes) scatters even similar keys uniformly.

- ✓ Load spreads evenly.
- ✗ Range queries lose their locality: adjacent keys end up on different partitions.

Cassandra compromises with a **compound primary key**. The first column is hashed to choose the partition; the rest sort data within it. That's efficient for "all posts by user 42, newest first."

Next, a short check on what you just read.
