# Batch and Stream Processing

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

## Streams: logs as the core abstraction

A **stream** is batch processing on unbounded data, handling events as they happen. The central abstraction is the **log**, the same append-only structure you built in lesson 13, which you met as a message broker in the last lesson. Three of its properties matter most for derived data:

- **Ordered by key**: partition by key, such as user id, and each key's events stay in order.
- **Retained, not deleted**: a new consumer can start from the beginning and rebuild its state from history.
- **Resumable**: a crashed, slow, or failed consumer picks up from its committed offset and catches up.

### Change data capture and the outbox

A tempting way to keep a search index in sync is a **dual write**: the application writes to the database, then writes the same change to the search index. It's broken:

- If the second write fails (the index is down or the process crashes), the stores **silently diverge** forever.
- Two concurrent dual writes can reach the two stores in **different orders**.

The fix is to make the database the **single source of ordered changes**:

- **Change data capture (CDC)** reads the database's replication log (Debezium does this for PostgreSQL and MySQL) and publishes every committed change, in commit order, to a Kafka topic. Each derived store consumes the topic at its own pace. If one is down, its consumer resumes from its offset when it returns. Nothing is lost.
- **The transactional outbox**: in the *same transaction* as the business change, insert an event row into an `outbox` table. A relay (often CDC itself) publishes outbox rows to Kafka. Because the event commits atomically with the data, the database and the event stream can never disagree.

**Event sourcing** goes further and makes the log of events the system of record itself, deriving every current-state view from it.

You'll wire up CDC in the simulator in the next lesson.

### Stream processing

Consumers transform streams continuously:

- **Windowed aggregations**: requests per minute, or p99 latency over the last 5 minutes. Windows can be *tumbling* (fixed), *hopping*, *sliding*, or *session* windows. Use **event time** (when it happened), not processing time, and handle stragglers that arrive late.
- **Joins**: stream–stream joins (match a search with the click that followed it), stream–table joins (enrich each event from a CDC-maintained table), and table–table joins (maintain a materialized view).

## Exactly-once semantics

Failures make consumers retry, so messages get processed **at least once**. Duplicates are inevitable at the transport level. What you can achieve is **effectively once**: the final *effect* is as if each message were processed once.

- **Idempotent writes**: make processing a message twice harmless. "Set balance to 120" is idempotent; "add 20" isn't. Store each message's offset or a unique id with the result, and skip messages you've already applied.
- **Atomic commit of output and offset**: write the results and the consumer's new offset in one transaction. Kafka transactions and Flink checkpoints do this.
- **Deduplication** by event id at the sink.

The guarantee is **end-to-end**: if any step in the chain isn't idempotent or transactional, duplicates leak through, so idempotency keys must flow all the way from the client.

## Key terms

| Term | Meaning |
|---|---|
| System of record / derived data | The source of truth / data computed from it, rebuildable |
| MapReduce | Map to key-value pairs, shuffle by key, reduce each group |
| Log-based broker | A partitioned append-only log; consumers track offsets |
| Dual write | Writing one change to two systems separately; diverges on failure |
| Change data capture | Publishing a database's committed changes as a stream |
| Outbox | Events written in the same transaction as the data, then relayed |
| Effectively-once | At-least-once delivery plus idempotent or transactional processing |

Watching all of this in production, from consumer lag to the latency of each hop, is the subject of lesson 34.
