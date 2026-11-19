# Derived Data and Batch Processing

*Chapter 9 · Microservices and Data Flow.*

*Based on* Designing Data-Intensive Applications*, Chapters 10 to 12.*

*Based on* Designing Data-Intensive Applications*, Chapters 10–12.*

Real applications don't use one database. They combine a primary database with caches, search indexes, analytics warehouses, and recommendation models. Data is split into two kinds:

- The **system of record** (source of truth): where each fact is first written. Your primary database.
- **Derived data**: anything computed from it, such as a cache, a search index, or a materialized view. If derived data is lost, you can rebuild it from the source.

The question in Part III: **how do you keep derived data in sync with the source?**

## Batch processing: MapReduce

The Unix philosophy (small tools, a uniform interface of text streams, and pipes) solves surprising problems:

```bash
cat access.log | awk '{print $7}' | sort | uniq -c | sort -rn | head -5   # top 5 URLs
```

**MapReduce** applies the same idea to thousands of machines and files in a distributed filesystem (HDFS):

1. **Map**: read input records and emit `(key, value)` pairs. For example, `(url, 1)` for each log line.
2. **Shuffle**: the framework sorts and groups pairs by key, sending all the values for a key to the same reducer.
3. **Reduce**: process all the values for one key. For example, sum them to get `(url, count)`.

Batch jobs treat their input as **immutable** and write **new** output, so a failed job can simply be rerun. If a machine dies, its task restarts elsewhere. Joins happen in the shuffle: send users and their events to the same reducer by user id. Newer **dataflow engines** (Spark, Flink) chain many operators and keep intermediate state in memory, so they're much faster than a pipeline of MapReduce jobs.

Batch output is derived data too: search indexes, recommendation models, and reports. The catch is **latency**: a nightly job's output is up to a day old.

Next, a short check on what you just read.
