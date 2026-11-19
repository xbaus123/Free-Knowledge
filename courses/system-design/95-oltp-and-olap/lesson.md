# OLTP, OLAP, and Column Storage

*Chapter 3 · Data Models and Storage Engines.*

## OLTP vs. OLAP

Storage engines also split by **access pattern**:

| | OLTP (transaction processing) | OLAP (analytics) |
|---|---|---|
| Typical query | Fetch a few records by key | Aggregate over millions of rows |
| Writes | Random-access, low-latency writes from users | Bulk import (ETL) or event streams |
| Used by | End users, through the application | Analysts and dashboards |
| Data | The current state | The history of events |
| Size | Gigabytes to terabytes | Terabytes to petabytes |

Analytics workloads moved to separate **data warehouses**, loaded through **ETL** (extract, transform, load) so they can't slow down the production database. Warehouses often use a **star schema**: a large **fact table** of events (each sale) surrounded by **dimension tables** (product, store, date).

Warehouses also store data in **columns** instead of rows. A query that reads 3 columns of a 100-column table only touches those 3 files. Each column holds similar values, so it compresses extremely well (bitmaps, run-length encoding). Parquet, BigQuery, Snowflake, Redshift, and ClickHouse all work this way.

## Key terms

| Term | Meaning |
|---|---|
| Log | An append-only sequence of records |
| Tombstone | A record marking a key as deleted |
| Segment | One file of the log; closed segments are immutable |
| Compaction | Rewriting segments to drop overwritten and deleted values |
| SSTable | A segment sorted by key, with a sparse index |
| Memtable | The in-memory sorted buffer of recent writes |
| LSM-tree | Memtable + SSTables + background compaction |
| B-tree | A tree of fixed-size pages, updated in place, with a WAL |
| Write amplification | Bytes written to disk per byte the application writes |

Next, a short check on what you just read.
