# Observability: Metrics, Logs, and Traces

*Chapter 10 · Observability and the Capstone.*

Build what the observability readings described: histogram percentiles, trace trees and critical paths, structured log queries, and burn-rate alerts.

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
