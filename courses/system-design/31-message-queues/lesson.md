# Message Queues: Task Queues, Logs, and Consumer Groups

*Part III · Derived Data. Based on* Designing Data-Intensive Applications*, Chapter 11.*

So far, every interaction in your designs has been a **request and response**: a caller sends a request, waits, and gets an answer. That couples the two sides in time. If the receiver is slow, the caller waits. If it's down, the caller fails. If a thousand callers arrive at once, the receiver must handle a thousand requests at once.

A **message broker** breaks that coupling. A **producer** hands a message to the broker and moves on. A **consumer** takes it from the broker whenever it's ready. The broker is a buffer, a router, and a durable record in between. This lesson covers the two very different families of broker, how they distribute work, and what "delivered" really means.

## Why go asynchronous

- **Load leveling**: a burst of 10,000 sign-ups becomes a queue that workers drain at their own pace. The capstone uses exactly this: tweets are acknowledged at once, and the expensive fan-out happens behind a queue. So do the choreographed sagas of the last lesson, where each service reacts to the previous one's events.
- **Decoupling**: the producer doesn't know or care who consumes, how many consumers there are, or whether they're up right now.
- **Fan-out**: one event ("order placed") feeds many independent consumers: email, inventory, analytics, search.
- **Reliability**: if a consumer crashes mid-task, the broker redelivers the message to another one.

The cost: the producer no longer learns the outcome. "Accepted" isn't "done," and errors surface later and elsewhere, so you need dead-letter handling, monitoring of queue depth, and idempotent consumers.

## Two questions every messaging system answers

*Designing Data-Intensive Applications* frames any messaging system with two questions:

1. **What happens when producers send faster than consumers can process?** The system can **drop** messages, **buffer** them in a queue (in memory? on disk? what happens when that fills?), or apply **backpressure**, blocking the producer until there's room (TCP flow control and bounded Unix pipes do this).
2. **What happens when nodes crash or go offline?** Are messages lost? Durability means writing to disk and replicating, which costs throughput. Some applications (metrics sampling) can tolerate occasional loss, and others (payments) can't.

## Patterns: point-to-point and publish-subscribe

When several consumers read from one stream of messages, there are two basic patterns:

- **Load balancing (competing consumers, point-to-point)**: each message goes to **one** of the consumers. Add consumers to process faster. This is a **work queue**: resize images, send emails, charge cards.
- **Fan-out (publish-subscribe)**: each message goes to **all** subscribers. Each subscriber does something different with every event.

Real systems combine them: several independent *groups* each receive every message (fan-out), and within each group, consumers share the work (load balancing). AWS's classic pattern publishes to an SNS topic that fans out to several SQS queues, each drained by its own pool of workers.

## Family 1: Task queues (traditional message brokers)

RabbitMQ (the AMQP standard), ActiveMQ, and Amazon SQS behave like a queue of individual messages:

- A consumer **receives** a message, processes it, and **acknowledges** it. Only then does the broker **delete** it.
- If the consumer crashes or doesn't acknowledge in time, the broker **redelivers** the message to another consumer. In SQS, a received message is hidden for a **visibility timeout**. If it isn't deleted before the timeout ends, it reappears.
- Messages are deleted once processed, so the broker holds only the backlog and works best when queues are short. Slow consumers make the queue grow, and throughput degrades as it spills to disk.
- Brokers can **route** flexibly. RabbitMQ's exchanges send a message to queues by exact key, by topic pattern (`orders.*.eu`), or to all bound queues.
- Extras: per-message **delays**, **priorities**, and **dead-letter queues**.

Consequences to design around:

- **At-least-once delivery.** A consumer can finish the work and then crash before its acknowledgment arrives, or run past the visibility timeout. The broker redelivers, and the work happens twice. So consumers must be **idempotent**: charge the card only if this payment id hasn't been charged.
- **A late acknowledgment can be refused.** If the visibility timeout expired and another consumer received the message, the first consumer's acknowledgment is for a delivery that no longer counts. (It's the lease problem from lesson 26 again.) Long tasks must **extend** their visibility timeout as they go.
- **Ordering is lost.** With competing consumers and redelivery, message 2 can finish before message 1. Even a single consumer sees reordering when a message is redelivered after later ones were processed.
- **Poison messages**: a message that crashes its consumer every time would be redelivered forever, blocking capacity. After N failed deliveries, move it to a **dead-letter queue (DLQ)** for a human to inspect.

## Family 2: Log-based brokers

Kafka, Amazon Kinesis, Apache Pulsar, and Redpanda take a different approach: the broker is an **append-only log on disk**, the same structure as your storage engine in lesson 13.

- A **topic** is split into **partitions**. Each partition is a log, and each message gets a sequential **offset** within its partition.
- A producer appends. The partition is chosen by **hashing the message key** (say, the user id), so all messages for a key land in one partition, **in order**. Messages without a key are spread round robin.
- Consumers **read** sequentially and track their position as an offset. **Reading doesn't delete anything.** Messages are retained for a configured time (days, weeks) or size, then old segments are discarded, like a circular buffer on disk.

### Consumer groups

To share work, consumers form a **consumer group**. The broker assigns each partition to exactly **one** consumer in the group (a consumer can own several partitions):

- Within a partition, messages are processed **in order** by one consumer.
- Parallelism is capped by the number of partitions: 8 partitions support at most 8 busy consumers per group. Extra consumers sit idle as hot standbys.
- **Every group gets every message**: a search indexer group and an email group each read the whole topic independently, at their own pace. That's publish-subscribe for free.

The group **commits** its offsets periodically, recording "everything before offset 1,042 in partition 3 is done." When consumers join, leave, or crash, the group **rebalances**: partitions are reassigned, and each new owner resumes from the **last committed offset**. Anything processed but not yet committed is processed **again**, so delivery is again at least once.

Kafka's default **range assignor** sorts consumers by name and gives each a contiguous block of partitions: with 7 partitions and 3 consumers, `[0, 1, 2]`, `[3, 4]`, `[5, 6]`.

### Why logs

- **Throughput**: appending and reading sequentially is the fastest thing a disk does (lesson 3). One partition handles hundreds of megabytes per second.
- **Replay**: because messages remain after consumption, a new consumer can start from the beginning and build its state from history. A buggy consumer can be fixed and **rewound** to reprocess the last day. This is what makes logs the backbone of derived data in the next lessons.
- **Cheap fan-out**: adding a consumer group costs no broker writes. It's just another set of offsets.
- **Consumer lag** is easy to monitor: the distance between a partition's end offset and the group's committed offset. It tells you how far behind, and how stale, each consumer is (lesson 34).

The costs: ordering and parallelism are tied to partitioning. A slow message blocks every message behind it in its partition (**head-of-line blocking**), so logs suit high-volume streams of fairly uniform, fast-to-process messages, and fit poorly for long, individually expensive jobs.

### Commit before or after processing?

When a consumer commits its offset decides its guarantee:

| Strategy | If the consumer crashes | Guarantee |
|---|---|---|
| Commit, then process | Committed messages that weren't processed are skipped | **At most once** |
| Process, then commit | Processed messages that weren't committed are processed again | **At least once** |
| Commit offsets atomically with the output | Neither: output and progress move together | **Effectively once** |

At least once plus idempotent processing is the usual choice. The next lesson covers effectively-once processing and how to publish events reliably alongside database writes (the transactional outbox).

## Choosing

| | Task queue (RabbitMQ, SQS) | Log (Kafka, Kinesis) |
|---|---|---|
| Unit | Individual message, acknowledged one by one | Partition, read sequentially by offset |
| After processing | Deleted | Retained until expiry |
| Work sharing | Any consumer takes any message | One consumer per partition per group |
| Ordering | Not guaranteed | Per partition |
| Replay | No | Yes, by resetting offsets |
| Best for | Jobs of varying cost, individual retries, delays and priorities | High-volume event streams, multiple subscribers, rebuilding state |

## Your task

`solution.py` builds one broker of each kind. Time is passed in as `now`, so nothing sleeps.

### 1. A task queue

`TaskQueue(visibility_timeout=30, max_receives=3)`:

- `send(body)` adds a message and returns its id.
- `receive(now)` delivers the **oldest visible** message as `(id, body, receipt)`, or returns `None`. The message is hidden until `now + visibility_timeout`. Every delivery gets a new, unique `receipt`.
- `ack(receipt)` deletes the message and returns `True`. A receipt from an earlier delivery of a message that has since been delivered again is stale: return `False` and delete nothing.
- `nack(receipt, now)` makes the message visible again at once (the consumer gave up), keeping its place in line.
- A message already delivered `max_receives` times is a poison message. When it would be delivered again, move its body to `dead_letters` and deliver the next message instead.

### 2. A partitioned log

`Topic(partitions)`:

- `publish(key, value)` appends to partition `stable_hash(key) % partitions`, or round robin starting at partition 0 when `key` is `None`. Return `(partition, offset)`.
- `read(partition, offset, max_messages=100)` returns `[(offset, key, value), ...]` without removing anything.
- `end_offset(partition)` is the offset the next message will get.

### 3. Consumer groups

`ConsumerGroup(topic)`:

- `join(consumer)` and `leave(consumer)` rebalance with the range assignor: sort the consumers, give each `partitions // consumers` partitions, plus one extra for the first `partitions % consumers`. After a rebalance, **every** partition's position goes back to its **committed** offset.
- `assignment(consumer)` lists its partitions in order.
- `poll(consumer, max_messages=10)` returns up to `max_messages` records as `(partition, offset, key, value)`, going through the consumer's partitions in order and continuing where the last poll stopped.
- `commit(consumer)` records the consumer's current position in each partition it owns.
- `lag()` is the total of end offset minus committed offset, over all partitions.

The tests check, among other things, that records processed but not committed before a rebalance are delivered again, and that two groups each see every message.

## Key terms

| Term | Meaning |
|---|---|
| Producer / consumer | Sends messages / receives and processes them |
| Backpressure | Slowing producers down when consumers can't keep up |
| Competing consumers | Each message goes to one of several consumers |
| Publish-subscribe | Each message goes to every subscriber |
| Visibility timeout | How long a received message stays hidden before redelivery |
| Dead-letter queue | Where messages go after failing too many times |
| Partition | One ordered, append-only log within a topic |
| Offset | A message's position in its partition |
| Consumer group | Consumers sharing a topic's partitions, with one shared set of offsets |
| Rebalance | Reassigning partitions when the group's members change |
| Consumer lag | Messages published but not yet processed |
| At-least-once | Nothing is lost, but some messages are processed twice |
