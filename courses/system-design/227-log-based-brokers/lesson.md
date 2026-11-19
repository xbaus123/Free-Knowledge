# Log-Based Brokers and Consumer Groups

*Chapter 9 · Microservices and Data Flow.*

## Family 2: Log-based brokers

Kafka, Amazon Kinesis, Apache Pulsar, and Redpanda take a different approach: the broker is an **append-only log on disk**, the same structure as your storage engine in chapter 3.

- A **topic** is split into **partitions**. Each partition is a log, and each message gets a sequential **offset** within its partition.
- A producer appends. The partition is chosen by **hashing the message key** (say, the user id), so all messages for a key land in one partition, **in order**. Messages without a key are spread round robin.
- Consumers **read** sequentially and track their position as an offset. **Reading doesn't delete anything.** Messages are retained for a configured time (days, weeks) or size, then old segments are discarded, like a circular buffer on disk.

## Consumer groups

To share work, consumers form a **consumer group**. The broker assigns each partition to exactly **one** consumer in the group (a consumer can own several partitions):

- Within a partition, messages are processed **in order** by one consumer.
- Parallelism is capped by the number of partitions: 8 partitions support at most 8 busy consumers per group. Extra consumers sit idle as hot standbys.
- **Every group gets every message**: a search indexer group and an email group each read the whole topic independently, at their own pace. That's publish-subscribe for free.

The group **commits** its offsets periodically, recording "everything before offset 1,042 in partition 3 is done." When consumers join, leave, or crash, the group **rebalances**: partitions are reassigned, and each new owner resumes from the **last committed offset**. Anything processed but not yet committed is processed **again**, so delivery is again at least once.

Kafka's default **range assignor** sorts consumers by name and gives each a contiguous block of partitions: with 7 partitions and 3 consumers, `[0, 1, 2]`, `[3, 4]`, `[5, 6]`.

Next, a short check on what you just read.
