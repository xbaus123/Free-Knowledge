# Exactly-Once Semantics

*Chapter 9 · Microservices and Data Flow.*

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

Watching all of this in production, from consumer lag to the latency of each hop, is the subject of chapter 10.

Next, a short check on what you just read.
