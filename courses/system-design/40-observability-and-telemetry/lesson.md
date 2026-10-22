# Observability: Metrics, Logs, and Traces

Every system in this course fails sometimes: a replica lags, a cache stampedes, a consumer falls behind, a partition heals and a zombie leader writes. In the simulator, you could replay each run and watch the nodes glow. In production, you only see what your system **tells** you. **Observability** is the property of a system that lets you understand what's happening inside it from the outside, using the data it emits, including problems nobody predicted.

**Monitoring** asks known questions: is the error rate above 1%? Is the disk 90% full? **Observability** lets you ask new questions after something strange happens: why are checkout requests from one region, on the newest app version, slow only when they touch the recommendations service? You need monitoring for the failures you expect, and observability for the ones you don't. Both rest on three kinds of telemetry: **metrics**, **logs**, and **traces**.

| Signal | What it is | Answers | Cost profile |
|---|---|---|---|
| **Metrics** | Numbers aggregated over time | *Is* something wrong? How much, since when? | Cheap: fixed size, whatever the traffic |
| **Logs** | Timestamped records of individual events | *What* happened in this request? | Grows with traffic and verbosity |
| **Traces** | One request's path through every service, as timed spans | *Where* is the time going? Which hop failed? | Grows with traffic, so usually sampled |

## Metrics

A metric is a named number sampled over time, forming a **time series**, stored in a time-series database (lesson 20). Four basic types:

- **Counter**: only goes up (resetting to zero on restart): requests served, errors, bytes sent. You almost never look at the raw value. You look at its **rate**: requests per second over the last 5 minutes.
- **Gauge**: goes up and down: queue length, memory in use, active connections, consumer lag.
- **Histogram**: counts observations into **buckets** by value: how many requests took ≤ 100 ms, ≤ 250 ms, ≤ 500 ms, and so on. From the buckets you can estimate **percentiles**.
- **Summary**: percentiles computed in the client itself. They're accurate, but can't be combined across instances.

### Labels and cardinality

Metrics carry **labels** (dimensions): `http_requests_total{method="GET", route="/cart", status="500"}`. Each distinct combination of label values is a separate time series. That's powerful (slice errors by route, by region, by version) and dangerous: label by `user_id` and a million users become a million time series. **Cardinality** (the number of series) is the main cost driver of a metrics system. Keep labels to small, bounded sets, and put unbounded values like user ids, request ids, and URLs with ids in them into logs and traces instead.

### Percentiles need histograms

Lesson 1 showed why you care about p99, not the mean. Here's the operational catch: **you can't average percentiles**. If server A's p99 is 100 ms and server B's is 900 ms, the fleet's p99 is not 500 ms. It depends on how many requests each served and on the full shape of both distributions. Histograms solve this. Bucket counts *can* be added across servers, and the percentile is estimated from the combined buckets:

1. Find the **rank**: for p90 of 1,000 requests, the 900th fastest.
2. Walk the buckets cumulatively to find the bucket containing that rank.
3. **Interpolate linearly** within the bucket, assuming its observations are spread evenly between its lower and upper bounds.

The estimate is only as precise as the buckets, so place bucket bounds around the latencies you care about, especially your SLO threshold. If the rank falls in the final `+Inf` bucket, the best you can say is "at least the highest bound."

### Prometheus and Grafana

**Prometheus**, the most widely used open-source metrics system, **pulls**: each service exposes a plain-text `/metrics` endpoint, and Prometheus **scrapes** it every 15 seconds or so:

```text
# HELP http_requests_total Requests handled.
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 1027
http_requests_total{method="POST",status="500"} 3
# HELP http_request_duration_seconds Request latency.
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 4
http_request_duration_seconds_bucket{le="0.25"} 8
http_request_duration_seconds_bucket{le="+Inf"} 10
http_request_duration_seconds_sum 2.2
http_request_duration_seconds_count 10
```

Histogram buckets are **cumulative**: each `le` ("less than or equal") count includes everything below it. You query with PromQL, for example the fleet-wide p99 over 5 minutes:

```promql
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

Pulling makes it easy to tell a dead target (the scrape fails) from an idle one. Short-lived batch jobs that finish before a scrape **push** to a gateway instead, and systems like StatsD and many SaaS vendors are push-based throughout. **Grafana** draws dashboards from Prometheus and many other sources.

### What to measure

Three checklists cover most services:

- **RED**, for request-driven services: **R**ate (requests per second), **E**rrors (failed requests per second), **D**uration (latency histograms).
- **USE**, for resources (CPUs, disks, connection pools, queues): **U**tilization (busy fraction), **S**aturation (work waiting: queue length), **E**rrors. That's exactly what the simulator's node badges show.
- Google's **four golden signals**: latency, traffic, errors, and saturation.

For asynchronous pipelines, add **consumer lag** for every consumer group (lesson 37): it's the stream version of queue length, and it tells you how stale every piece of derived data is.

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

### Context propagation

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

### Reading a trace: the critical path

In a trace, not every slow span matters. If a handler calls three services in parallel and waits for all of them, the request is as slow as the **slowest** branch, and speeding up the others changes nothing. The **critical path** is the chain of spans that actually determined the end-to-end latency. A good approximation: start at the root, step to the child that finished **last**, and repeat. Optimize along the critical path, and nowhere else.

### Sampling

Tracing every request at high traffic is expensive. **Head sampling** decides at the root (say, keep 1%) and propagates the decision in the flags, so a trace is kept or dropped whole. It's cheap, but it drops the rare slow or failed requests you most want to see. **Tail sampling** buffers complete traces in a collector and decides afterward: keep every error, every trace above the p99, and 1% of the rest. It costs more, but keeps the interesting traces.

## OpenTelemetry

**OpenTelemetry (OTel)** is the vendor-neutral standard for producing telemetry, a merger of the earlier OpenTracing and OpenCensus projects:

- **APIs and SDKs** for every major language to create metrics, logs, and spans.
- **Auto-instrumentation** for common frameworks (HTTP servers and clients, database drivers, Kafka clients), so many spans and metrics appear with no code changes, and context propagates automatically.
- **Semantic conventions**: standard attribute names such as `http.request.method` and `db.system`, so dashboards work across services and languages.
- **OTLP**, a wire protocol, and the **Collector**, an agent that receives telemetry, batches, filters, and tail-samples it, and exports it to any backend: Prometheus, Jaeger, Grafana Tempo, or a commercial vendor.

Instrument once with OpenTelemetry, and you can change backends without touching application code.

### Connecting the pillars

The three signals are most useful linked together. A latency spike on a dashboard (metric) links to **exemplars**, sample trace ids recorded alongside histogram buckets. The trace shows the slow span. The span's trace id finds every log line written during it. That path, from "something's wrong" to "here's the exact line," is the practical meaning of observability.

## SLOs and alerting

You can't page a human for every anomaly. Alert on **symptoms users feel**, not on causes like CPU usage.

- An **SLI** (service level indicator) is a measurement: the fraction of requests that succeed in under 300 ms.
- An **SLO** (objective) is a target for it: 99.9% over 30 days.
- The **error budget** is what the SLO allows to fail: 0.1% of requests, about 43 minutes of total outage a month. Spending it on risky launches is fine. Running out means slowing down and fixing reliability.

The **burn rate** is how fast you're spending the budget: the observed error ratio divided by the allowed ratio (1 − SLO). A burn rate of 1 spends exactly the whole budget over the SLO window. A burn rate of 14.4 spends 2% of a 30-day budget in one hour, and would exhaust it in about two days.

**Multi-window burn-rate alerts** (from Google's SRE workbook) page when *both* a long window (say 1 hour) and a short window (say 5 minutes) burn above a threshold. The long window ensures enough budget was spent to matter, so a brief blip doesn't page anyone. The short window ensures the problem is still happening, so the alert clears quickly after recovery.

## Your task

`solution.py` has four independent parts. `Counter`, the formatting helpers, `Span`, and `Tracer.new_id` are provided.

### 1. Metrics

- `Histogram(name, help, buckets)`: `observe(value, **labels)` counts the value in the first bucket whose bound is **≥** the value (there's an implicit `+Inf` bucket), and tracks each label set's `sum` and `count` separately.
- `quantile(q, **labels)` estimates the percentile with the interpolation above. The first bucket's lower bound is 0. If the rank lands in `+Inf`, return the highest finite bound. Return `None` for a label set with no observations.
- `render(metrics)` produces the Prometheus text format shown above, for a list of `Counter`s and `Histogram`s: `# HELP` and `# TYPE` lines per metric, one line per series, label sets in sorted order, labels sorted by name, histogram buckets **cumulative** with `le` as the last label, then `_sum` and `_count`. Format numbers with `fmt` and labels with `_labels`. End with a newline.

### 2. Traces

- `Tracer.start_span(name, now, parent=None)`: with no parent, a new 32-hex-digit trace id. With a parent (a `Span` or a `SpanContext`), its trace id, and its span id as `parent_id`. Every span gets a new 16-hex-digit span id and is appended to `tracer.spans`.
- `inject(span, headers)` adds `traceparent: 00-<trace id>-<span id>-01` and returns the headers.
- `extract(headers)` returns a `SpanContext` for a valid `traceparent`: version `00`, lowercase hex digits of exactly the right lengths, and ids that aren't all zeros. Otherwise, `None`.
- `critical_path(spans)` takes one trace's finished spans in any order. Start at the root (the span whose parent isn't among them) and repeatedly step to the child with the latest `end`. Return the names.

### 3. Logs

`log_line(level, message, span=None, **fields)` returns one line of JSON with sorted keys: `level`, `msg`, the extra fields, and, when there's a span, its `trace_id` and `span_id`.

### 4. SLO alerts

- `burn_rate(errors, requests, slo)`: the error ratio divided by `1 - slo` (0 when there were no requests).
- `should_page(short_window, long_window, slo, threshold=14.4)`: each window is `(errors, requests)`. Page only if **both** burn at the threshold or faster.

## Key terms

| Term | Meaning |
|---|---|
| Observability | Understanding a system's internal state from the telemetry it emits |
| Counter / gauge / histogram | Only up / up and down / bucketed distribution |
| Cardinality | The number of distinct time series a metric's labels create |
| Scrape | Prometheus pulling a target's `/metrics` endpoint |
| RED / USE | Rate, errors, duration / utilization, saturation, errors |
| Structured log | A log line made of machine-readable fields |
| Trace / span | One request's journey / one timed operation within it |
| Context propagation | Passing trace and span ids along with each request |
| Critical path | The chain of spans that determined total latency |
| Head / tail sampling | Deciding to keep a trace at its start / after it completes |
| SLI / SLO / error budget | A measurement / a target for it / the failures the target allows |
| Burn rate | How fast errors spend the error budget |
