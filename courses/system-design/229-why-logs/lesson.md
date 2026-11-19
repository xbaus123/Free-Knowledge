# Why Logs, Commit Order, and Choosing a Broker

*Chapter 9 · Microservices and Data Flow.*

## Why logs

- **Throughput**: appending and reading sequentially is the fastest thing a disk does (chapter 1). One partition handles hundreds of megabytes per second.
- **Replay**: because messages remain after consumption, a new consumer can start from the beginning and build its state from history. A buggy consumer can be fixed and **rewound** to reprocess the last day. This is what makes logs the backbone of derived data in the rest of this chapter.
- **Cheap fan-out**: adding a consumer group costs no broker writes. It's just another set of offsets.
- **Consumer lag** is easy to monitor: the distance between a partition's end offset and the group's committed offset. It tells you how far behind, and how stale, each consumer is (chapter 10).

The costs: ordering and parallelism are tied to partitioning. A slow message blocks every message behind it in its partition (**head-of-line blocking**), so logs suit high-volume streams of fairly uniform, fast-to-process messages, and fit poorly for long, individually expensive jobs.

## Commit before or after processing?

When a consumer commits its offset decides its guarantee:

| Strategy | If the consumer crashes | Guarantee |
|---|---|---|
| Commit, then process | Committed messages that weren't processed are skipped | **At most once** |
| Process, then commit | Processed messages that weren't committed are processed again | **At least once** |
| Commit offsets atomically with the output | Neither: output and progress move together | **Effectively once** |

At least once plus idempotent processing is the usual choice. The stream processing readings cover effectively-once processing and how to publish events reliably alongside database writes (the transactional outbox).

## Choosing

| | Task queue (RabbitMQ, SQS) | Log (Kafka, Kinesis) |
|---|---|---|
| Unit | Individual message, acknowledged one by one | Partition, read sequentially by offset |
| After processing | Deleted | Retained until expiry |
| Work sharing | Any consumer takes any message | One consumer per partition per group |
| Ordering | Not guaranteed | Per partition |
| Replay | No | Yes, by resetting offsets |
| Best for | Jobs of varying cost, individual retries, delays and priorities | High-volume event streams, multiple subscribers, rebuilding state |

Next, a short check on what you just read.
