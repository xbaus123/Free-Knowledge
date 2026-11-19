# Downsampling, Retention, and Picking a TSDB

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

## Downsampling and retention

Nobody needs 15-second resolution for last year's CPU usage. **Downsampling** rolls raw points up into coarser buckets, and **retention tiers** keep each resolution for a different time:

| Resolution | Kept for | Used for |
|---|---|---|
| Raw (15 s) | 15 days | Debugging today's incident |
| 5-minute rollups | 90 days | Week-over-week comparisons |
| 1-hour rollups | 5 years | Capacity planning and trends |

What a rollup stores matters. Store **min, max, sum, and count** for each bucket, not just the average. Averages can't be combined correctly without counts (the average of two averages is wrong when buckets hold different numbers of points), and the max is what reveals a spike that an average smooths away. Percentiles can't be rolled up from percentiles at all, so roll up histogram buckets instead (chapter 10).

Prometheus does this with recording rules, and TimescaleDB with **continuous aggregates** that update incrementally as data arrives. Long-term metrics systems like Thanos and Grafana Mimir upload compacted blocks to an **object store** and downsample them there, joining the two halves of this chapter's storage readings: the TSDB for recent, hot data, the object store for cheap, durable history.

## Picking a TSDB

- **Prometheus**: pull-based monitoring, a single node per server, with Thanos, Mimir, or Cortex for scale and long-term storage.
- **InfluxDB** and **VictoriaMetrics**: purpose-built engines, push or pull, high compression.
- **TimescaleDB**: a PostgreSQL extension that partitions tables by time into **chunks** automatically, keeping SQL, joins, and transactions.
- **ClickHouse** and other columnar warehouses: often used for time series with high-cardinality labels, like events per user.

In all of them, the failure mode to watch is **cardinality**: every distinct label combination is a separate series with its own index entries and chunks, so a label with unbounded values (user ids, request ids) multiplies memory use until the database falls over.

Next, a short check on what you just read.
