# Critical Paths, Sampling, and OpenTelemetry

*Chapter 10 · Observability and the Capstone.*

## Reading a trace: the critical path

In a trace, not every slow span matters. If a handler calls three services in parallel and waits for all of them, the request is as slow as the **slowest** branch, and speeding up the others changes nothing. The **critical path** is the chain of spans that actually determined the end-to-end latency. A good approximation: start at the root, step to the child that finished **last**, and repeat. Optimize along the critical path, and nowhere else.

## Sampling

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

Next, a short check on what you just read.
