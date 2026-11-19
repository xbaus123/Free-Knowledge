# Streams, Change Data Capture, and the Outbox

*Chapter 9 · Microservices and Data Flow.*

## Streams: logs as the core abstraction

A **stream** is batch processing on unbounded data, handling events as they happen. The central abstraction is the **log**, the same append-only structure you built in chapter 3, which you met as a message broker in the messaging readings. Three of its properties matter most for derived data:

- **Ordered by key**: partition by key, such as user id, and each key's events stay in order.
- **Retained, not deleted**: a new consumer can start from the beginning and rebuild its state from history.
- **Resumable**: a crashed, slow, or failed consumer picks up from its committed offset and catches up.

## Change data capture and the outbox

A tempting way to keep a search index in sync is a **dual write**: the application writes to the database, then writes the same change to the search index. It's broken:

- If the second write fails (the index is down or the process crashes), the stores **silently diverge** forever.
- Two concurrent dual writes can reach the two stores in **different orders**.

The fix is to make the database the **single source of ordered changes**:

- **Change data capture (CDC)** reads the database's replication log (Debezium does this for PostgreSQL and MySQL) and publishes every committed change, in commit order, to a Kafka topic. Each derived store consumes the topic at its own pace. If one is down, its consumer resumes from its offset when it returns. Nothing is lost.
- **The transactional outbox**: in the *same transaction* as the business change, insert an event row into an `outbox` table. A relay (often CDC itself) publishes outbox rows to Kafka. Because the event commits atomically with the data, the database and the event stream can never disagree.

**Event sourcing** goes further and makes the log of events the system of record itself, deriving every current-state view from it.

You'll wire up CDC in the simulator at the end of this chapter.

## Stream processing

Consumers transform streams continuously:

- **Windowed aggregations**: requests per minute, or p99 latency over the last 5 minutes. Windows can be *tumbling* (fixed), *hopping*, *sliding*, or *session* windows. Use **event time** (when it happened), not processing time, and handle stragglers that arrive late.
- **Joins**: stream–stream joins (match a search with the click that followed it), stream–table joins (enrich each event from a CDC-maintained table), and table–table joins (maintain a materialized view).

Next, a short check on what you just read.
