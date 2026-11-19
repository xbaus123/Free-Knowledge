# Observability and Metrics

*Chapter 10 · Observability and the Capstone.*

Every system in this course fails sometimes: a replica lags, a cache stampedes, a consumer falls behind, a partition heals and a zombie leader writes. In the simulator, you could replay each run and watch the nodes glow. In production, you only see what your system **tells** you. **Observability** is the property of a system that lets you understand what's happening inside it from the outside, using the data it emits, including problems nobody predicted.

**Monitoring** asks known questions: is the error rate above 1%? Is the disk 90% full? **Observability** lets you ask new questions after something strange happens: why are checkout requests from one region, on the newest app version, slow only when they touch the recommendations service? You need monitoring for the failures you expect, and observability for the ones you don't. Both rest on three kinds of telemetry: **metrics**, **logs**, and **traces**.

| Signal | What it is | Answers | Cost profile |
|---|---|---|---|
| **Metrics** | Numbers aggregated over time | *Is* something wrong? How much, since when? | Cheap: fixed size, whatever the traffic |
| **Logs** | Timestamped records of individual events | *What* happened in this request? | Grows with traffic and verbosity |
| **Traces** | One request's path through every service, as timed spans | *Where* is the time going? Which hop failed? | Grows with traffic, so usually sampled |

## Metrics

A metric is a named number sampled over time, forming a **time series**, stored in a time-series database (chapter 4). Four basic types:

- **Counter**: only goes up (resetting to zero on restart): requests served, errors, bytes sent. You almost never look at the raw value. You look at its **rate**: requests per second over the last 5 minutes.
- **Gauge**: goes up and down: queue length, memory in use, active connections, consumer lag.
- **Histogram**: counts observations into **buckets** by value: how many requests took ≤ 100 ms, ≤ 250 ms, ≤ 500 ms, and so on. From the buckets you can estimate **percentiles**.
- **Summary**: percentiles computed in the client itself. They're accurate, but can't be combined across instances.

## Labels and cardinality

Metrics carry **labels** (dimensions): `http_requests_total{method="GET", route="/cart", status="500"}`. Each distinct combination of label values is a separate time series. That's powerful (slice errors by route, by region, by version) and dangerous: label by `user_id` and a million users become a million time series. **Cardinality** (the number of series) is the main cost driver of a metrics system. Keep labels to small, bounded sets, and put unbounded values like user ids, request ids, and URLs with ids in them into logs and traces instead.

## Percentiles need histograms

Chapter 1 showed why you care about p99, not the mean. Here's the operational catch: **you can't average percentiles**. If server A's p99 is 100 ms and server B's is 900 ms, the fleet's p99 is not 500 ms. It depends on how many requests each served and on the full shape of both distributions. Histograms solve this. Bucket counts *can* be added across servers, and the percentile is estimated from the combined buckets:

1. Find the **rank**: for p90 of 1,000 requests, the 900th fastest.
2. Walk the buckets cumulatively to find the bucket containing that rank.
3. **Interpolate linearly** within the bucket, assuming its observations are spread evenly between its lower and upper bounds.

The estimate is only as precise as the buckets, so place bucket bounds around the latencies you care about, especially your SLO threshold. If the rank falls in the final `+Inf` bucket, the best you can say is "at least the highest bound."

Next, a short check on what you just read.
