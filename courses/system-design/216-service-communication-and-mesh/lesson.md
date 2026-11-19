# Service Communication and the Service Mesh

*Chapter 9 · Microservices and Data Flow.*

## Communication and its failure modes

Services talk in two styles:

- **Synchronous** request/response (REST or gRPC, chapter 1): simple to reason about, but the caller waits, and it fails if the callee fails. The services are **coupled in time**.
- **Asynchronous** events or messages through a broker (later in this chapter): the producer moves on, and consumers process when they can. Services stay up when their neighbors are down, at the cost of **eventual consistency** and harder debugging.

### Availability multiplies

If a request needs services A, B, and C to all be up, and each is up 99.9% of the time independently, the request succeeds only 99.9% × 99.9% × 99.9% ≈ 99.7% of the time. With 10 synchronous dependencies, it's 99.0%: about 7 hours of failures a month instead of 43 minutes. Latency adds up the same way along a chain, and fan-out amplifies tail latency (chapter 1).

So minimize **synchronous** dependencies on the critical path. Cache what you can. Make non-essential dependencies optional: if recommendations are down, show the page without them (**graceful degradation**). Move work that doesn't need to finish before the response behind a queue.

**Cycles** in the synchronous call graph are worse. If A calls B and B calls A, neither can be deployed or scaled on its own, a slowdown in either feeds back into both, and retries circle around until both are overloaded. A cycle is a sign that two services are really one, or that one direction of the call should be an event.

### Resilience patterns

Every remote call needs a plan for failure, and chapter 7 built the toolkit: **timeouts** and propagated **deadlines**, **retries** with backoff, jitter, and a budget (and only for idempotent operations), **circuit breakers** that stop calling a dependency that keeps failing, and **bulkheads** that keep one slow dependency from using up every thread. In a microservice architecture they stop being optional. With dozens of services, some dependency is always degraded, and these patterns are what keep that from spreading through the call graph. The question is where to put them: in a library inside every service, or in the network.

## Service mesh

Every service needs the same networking features: service discovery, load balancing, timeouts, retries, circuit breakers, mTLS (chapter 2), metrics, and tracing (chapter 10). Building them into a library works until your services are written in five languages, each needing its own version, upgraded in lockstep.

A **service mesh** moves those features out of the application into the network:

- The **data plane** is a **sidecar proxy**, usually Envoy, deployed next to every service instance. All of the instance's inbound and outbound traffic flows through it. The application calls `http://payments/charge` in plain HTTP, and the sidecar finds a healthy payments instance, opens an mTLS connection to *its* sidecar, applies timeouts and retries, and records metrics and trace spans.
- The **control plane** (Istio, Linkerd, Consul) configures every sidecar: routing rules, retry policies, which services may call which, and short-lived certificates for every workload's identity.

This gives you uniform behavior across languages, encryption and identity everywhere, and changes like "send 5% of traffic to v2" (**traffic shifting**, for canary releases) without touching application code. It's the client-side load balancing of chapter 2, done for every service at once. The costs: an extra proxy hop on every call (typically under a millisecond each way), CPU and memory for thousands of proxies, and a complex system of its own to operate. Newer "sidecarless" designs move the proxy into a shared per-node agent, or into the kernel with eBPF, to cut that overhead.

A mesh can't fix bad boundaries. And a mesh retrying a non-idempotent call still charges the customer twice.

Next, a short check on what you just read.
