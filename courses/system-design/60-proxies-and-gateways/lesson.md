# Reverse Proxies and API Gateways

*Chapter 2 · The Front Door.*

## Reverse proxies

A **forward proxy** acts on behalf of *clients* (a corporate proxy that filters outbound browsing). A **reverse proxy** acts on behalf of *servers*: clients think they're talking to the origin, but the proxy receives every request and forwards it. Every L7 load balancer is a reverse proxy, and reverse proxies do much more than balance:

- **TLS termination**: decrypt once at the edge, and manage certificates in one place (covered in the security readings).
- **Buffering slow clients**: a mobile client uploading at 50 KB/s would tie up an application worker for seconds. The proxy absorbs the slow upload and hands the backend a complete request in one burst. This also blunts slow-request attacks like Slowloris.
- **Compression and caching** of responses (chapter 5).
- **Protection**: request size limits, header normalization, and hiding the internal topology.

## API gateways

An **API gateway** is a reverse proxy specialized for the front door of an API, typically one built from many services. It handles cross-cutting concerns once, at the edge, so individual services don't each reimplement them:

- **Routing**: `/api/users/*` to the user service, `/api/orders/*` to the order service. Clients see one API, while the backend is many services that can be split, merged, or moved.
- **Authentication**: verify API keys or tokens (such as JWTs) once, and pass the verified identity to services in a header. The security lab builds exactly this.
- **Rate limiting and quotas** per client (chapter 6), rejecting floods before they reach anything expensive.
- **Transformation**: translate between protocols (REST outside, gRPC inside), version APIs, and reshape responses.
- **Aggregation**: one client call fans out to several services and returns a combined result. A **backend for frontend (BFF)** is a gateway tailored to one client, such as the mobile app.
- **Observability**: every request passes through, so the gateway is the natural place to record metrics, assign request ids, and start traces (chapter 10).
- **Traffic shifting**: send 1% of traffic to a new version (a **canary**) and watch its error rate before going further.

Gateways have failure modes of their own. Everything flows through them, so they must be highly available and fast. And the temptation to put business logic in the gateway turns it into a distributed monolith that every team must change. Keep it to cross-cutting concerns. For traffic *between* internal services (east-west, as opposed to north-south traffic from clients), a **service mesh** runs a small proxy (often Envoy) beside every service instance and applies the same features without a central gateway (chapter 9).

Next, a short check on what you just read.
