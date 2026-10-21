# Stream Processing: Change Data Capture

Your marketplace keeps product listings in **Postgres**, the system of record. Two derived stores hang off it:

- **Redis** caches listings, so reads rarely touch Postgres. API servers read and write through it.
- **Elasticsearch** powers search. Each API server **dual-writes**: after Postgres commits a change, the server sends the same change to Elasticsearch.

Load for this run:

- **1,200 requests in one second**: 70% reads, 30% writes.
- Sellers check their listing **30 ms after editing** it.
- At 300 ms, **Elasticsearch restarts for a version upgrade** and is down for 300 ms.

Click **Simulate Traffic** and look at the results.

## Two ways derived data drifts

**The search index loses updates.** Every dual write sent while Elasticsearch was down failed, and nobody retried it. When it comes back, those listings are missing or stale, and they'll stay that way until someone edits them again. The two stores have silently diverged.

**The cache serves old listings.** Writes pass through Redis to Postgres, but under the **expire after a TTL** policy, Redis keeps the old copy. A seller edits a listing, reloads, and sees the old version.

## Your task

Make Postgres the single, ordered source of changes, and feed every derived store from it:

1. Add a **Message Queue** (Kafka).
2. Double-click **Postgres** and turn on **Publish changes (outbox / CDC)**. Draw an edge **Postgres → Kafka**. Every committed write now becomes an event, in commit order, published only after the data is safely committed.
3. Connect **Kafka → Elasticsearch** and **Kafka → Redis**. Kafka delivers every event to each subscriber. Elasticsearch applies the change; Redis **deletes its cached copy**, so the next read loads the fresh value. If a subscriber is down, Kafka keeps the events and retries until it's back.
4. Remove the servers' direct edges to Elasticsearch. The dual write is no longer needed.

To pass:

- **Elasticsearch has every record up to date** at the end of the run, despite its restart.
- **Stale reads ≤ 1%.**
- **p99 latency ≤ 150 ms.**

Replay the run and watch Kafka's **backlog** grow while Elasticsearch is down, then drain as it catches up.

> **Think about it.** CDC makes the search index *eventually* consistent: there's a short window between the commit and the event being applied. Where would that window matter to users, and where wouldn't it? And what makes it safe for a consumer to process the same event twice after a crash? (Hint: "set listing 42 to version 7" is idempotent.)
