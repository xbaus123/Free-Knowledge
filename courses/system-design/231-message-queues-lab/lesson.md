# Message Queues: Task Queues, Logs, and Consumer Groups

*Chapter 9 · Microservices and Data Flow.*

Build what the messaging readings described: a task queue with visibility timeouts and dead letters, a partitioned log, and consumer groups.

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
