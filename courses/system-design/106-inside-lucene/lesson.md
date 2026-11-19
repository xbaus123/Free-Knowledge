# Inside Lucene

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

## Inside Lucene

Lucene is the Java library inside Elasticsearch, OpenSearch, and Solr. Its storage design should look familiar from chapter 3: it's a **log-structured** engine, and its files are **immutable segments**, much like SSTables.

- New documents go into an **in-memory buffer**.
- Every second or so, a **refresh** writes the buffer out as a new, small **segment**, a complete mini inverted index, and makes it searchable. That's why Elasticsearch is **near-real-time**: a document you just indexed may not appear in search for up to the refresh interval.
- Segments are opened but not yet fsynced to disk. For durability, Elasticsearch also appends every operation to a **translog**, a write-ahead log. A periodic **flush** fsyncs the segments and truncates the translog.
- A search runs against **every segment** and merges the results. Many small segments make searches slow, so a background **merge policy** combines segments into bigger ones, like compaction.
- Segments are never modified, so a **delete** only sets a bit in the segment's **live-docs bitmap**, a tombstone. An **update** is a delete plus an add. The deleted document's space is reclaimed when its segment is merged.

Immutability has the same benefits it had for SSTables: segments can be cached aggressively by the operating system, read without locks, and compressed heavily. The cost is write amplification from merging, and a refresh interval that trades freshness against indexing throughput.

An inverted index answers "which documents contain this term?" but is terrible at "what is document 7's price?", which sorting and aggregations need for every match. So Lucene also stores **doc values**: a **column-oriented** copy of chosen fields, one column per field, the column storage you met in chapter 3.

Next, a short check on what you just read.
