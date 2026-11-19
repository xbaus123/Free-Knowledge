# Logs and Distributed Tracing

*Chapter 10 · Observability and the Capstone.*

## Logs

A log is a timestamped record of a discrete event: "payment declined," "cache miss for user:42," "leader elected for term 7." Logs carry the detail metrics throw away.

- **Structure them.** `user 42 paid 19.99` is easy to write and painful to query. A JSON object with fields (`{"level": "info", "msg": "payment", "user_id": 42, "amount_cents": 1999}`) can be filtered, aggregated, and joined by machines.
- **Include correlation ids.** A request touches many services, and each writes its own logs. Stamp every log line with the **trace id** (below) so you can pull up every line, from every service, for one request.
- **Use levels** (debug, info, warn, error) and keep production at info. Debug logging in a hot loop can cost more than the work it describes.
- **Centralize** them: ship logs from every machine to a searchable store (Elasticsearch, Loki, a cloud service). A log on a server that's been replaced is a log you'll never read.
- **Sample and budget.** Log volume grows with traffic, and at scale storage cost is real. Sample successful requests and keep every error.

## Distributed tracing

Metrics tell you checkout's p99 jumped. Logs tell you what each service did. Neither tells you *where in the chain of calls* the time went. A **trace** does. The idea comes from Google's Dapper paper:

- A **trace** is one request's whole journey, identified by a **trace id**.
- A **span** is one timed operation within it: an HTTP handler, a database query, a cache lookup, a message being processed. Each span has its own **span id**, the **parent span id** of the operation that caused it, a start and end time, and attributes such as `http.route` and `db.statement`.
- Spans form a tree, usually drawn as a waterfall: the root at the top, and children indented beneath it along a shared time axis.

## Context propagation

For spans in different processes to join one trace, the trace context must travel **with the request**. The W3C **Trace Context** standard defines the `traceparent` header:

```text
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

| Part | Example | Meaning |
|---|---|---|
| Version | `00` | The format version |
| Trace id | `4bf92f35…0e4736` (32 hex digits) | The whole request's id |
| Parent id | `00f067aa0ba902b7` (16 hex digits) | The caller's span |
| Flags | `01` | Bit 0 set: this trace is sampled |

The caller **injects** its current span's context into outgoing request headers. The callee **extracts** it and starts its own span as a child. Ids of all zeros are invalid. The same header goes into message metadata when a request continues asynchronously through Kafka or a task queue, so traces don't stop at the broker.

Next, a short check on what you just read.
