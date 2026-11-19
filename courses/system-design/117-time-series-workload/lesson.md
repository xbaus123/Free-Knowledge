# Time-Series Databases: Workload and Layout

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

## The workload

A time series is a sequence of `(timestamp, value)` points for one **series**, identified by a metric name and labels, like `http_requests_total{service="api", status="500"}` (chapter 10). The workload has a distinctive shape:

- **Writes dominate**, and arrive at a huge, steady rate. 10,000 servers each exposing 500 metrics, scraped every 15 seconds, is 333,000 points per second, around the clock.
- Points arrive **nearly in time order**, and are almost **never updated or deleted** individually.
- Reads scan **time ranges** ("the last hour") and **aggregate across series** ("total error rate across all API servers").
- Recent data is queried constantly at full detail. Old data is queried rarely, at coarse resolution.

A general-purpose database with a row per point pays per-row overhead (a full timestamp, the labels, a row header) and an index update per insert. A log-structured engine (chapter 3) handles the write rate better. TSDBs go further and exploit the workload's regularity.

## Layout: series, blocks, and columns

Prometheus's storage engine is a good model of the design:

- An **inverted index** maps each label pair to the ids of series that have it, exactly the structure from earlier in this chapter. A query for `{service="api", status="500"}` intersects two postings lists to find its series.
- Recent data lives in an in-memory **head block**, protected by a write-ahead log. Each series' points are appended to its own **chunk**.
- Every two hours, the head is written out as an immutable **block**: a directory of compressed chunks plus its own index. Background **compaction** merges small blocks into larger ones covering longer time ranges.
- **Retention** deletes whole blocks once they're older than the limit. There are no per-point tombstones, so dropping a month of data is as cheap as deleting a directory.

Within a chunk, timestamps and values are stored and compressed **separately**, as columns: a column of timestamps that rise steadily, and a column of values that change slowly.

Next, a short check on what you just read.
