# Prometheus, and What to Measure

*Chapter 10 · Observability and the Capstone.*

## Prometheus and Grafana

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

## What to measure

Three checklists cover most services:

- **RED**, for request-driven services: **R**ate (requests per second), **E**rrors (failed requests per second), **D**uration (latency histograms).
- **USE**, for resources (CPUs, disks, connection pools, queues): **U**tilization (busy fraction), **S**aturation (work waiting: queue length), **E**rrors. That's exactly what the simulator's node badges show.
- Google's **four golden signals**: latency, traffic, errors, and saturation.

For asynchronous pipelines, add **consumer lag** for every consumer group (chapter 9): it's the stream version of queue length, and it tells you how stale every piece of derived data is.

Next, a short check on what you just read.
