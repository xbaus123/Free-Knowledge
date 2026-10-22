# Load Balancing, Reverse Proxies, and API Gateways

*Part I · Foundations.*

In the last lesson, you put a load balancer in front of two servers and the latency spike went away. That box did more than you might think. It decided which server got each request, noticed when one died, and hid from clients how many servers there were. This lesson opens the box: where load balancing happens, how the algorithms differ, how health checking works, and how a load balancer grows into a reverse proxy and then into an API gateway.

## Why balance load

A load balancer sits between clients and a pool of interchangeable **backends** and gives you three things:

1. **Scalability**: add a server, and the pool's capacity grows. Clients don't change anything.
2. **Availability**: when a backend dies, traffic flows to the others. Without a load balancer, every client pointed at the dead server fails.
3. **Indirection**: clients know one stable address. Behind it, you can deploy, resize, and replace servers freely. Most of the operational tricks in this course (rolling deployments in lesson 18, canary releases, failover) depend on this layer of indirection.

It only works cleanly when the backends are **stateless**: any server can handle any request because the state lives elsewhere, in a database or cache. Keeping session state on a server forces **sticky sessions** (routing each user back to "their" server), which spreads load unevenly and loses sessions when that server dies. Move the state out and the servers become cattle, not pets.

## Where balancing happens

Load can be spread at several layers, and big systems use most of them at once:

| Layer | How | Strengths | Weaknesses |
|---|---|---|---|
| **DNS** | Return different IP addresses for one name (lesson 2) | Free, global, works across regions | Clients and resolvers cache answers, so changes and failover lag by the TTL; no knowledge of load |
| **Anycast / ECMP** | Many sites announce the same IP; the network routes each client to the nearest | Spreads load across many load balancer machines | Coarse; can't see individual requests |
| **L4 load balancer** | Forwards TCP or UDP connections | Very fast, any protocol | Can't see HTTP; balances connections, not requests |
| **L7 load balancer** | Terminates HTTP and forwards each request | Content-aware routing and per-request balancing | More CPU per request; must understand the protocol |
| **Client-side** | Each client holds the server list and picks itself (gRPC, service meshes) | No extra hop | Every client needs the logic and an up-to-date server list |

### L4: transport-level balancing

A **layer 4** load balancer works with TCP and UDP. It sees addresses and ports, picks a backend when a connection opens, and then forwards every packet of that connection to the same backend. It never reads the bytes inside.

- It's fast and cheap. Linux IPVS, Google's Maglev, and AWS's Network Load Balancer handle millions of packets per second per machine, and with **direct server return** the backend's response skips the load balancer entirely.
- It works for any protocol: databases, message brokers, game servers.
- It balances **connections**, not requests. That's fine when connections are short. But HTTP/2 and gRPC multiplex thousands of requests over a few long-lived connections, so an L4 balancer can pin a huge share of traffic to one backend while others idle.

### L7: application-level balancing

A **layer 7** load balancer terminates the client's TCP (and usually TLS) connection, parses each HTTP request, and opens its own connection to a backend. It can therefore:

- balance **each request** independently, even within one long-lived client connection,
- **route by content**: host name, path, method, headers, or cookies (`/api/*` to API servers, `/static/*` to a file server),
- **retry** a failed request on another backend (only when it's idempotent; lesson 4),
- add headers such as `X-Forwarded-For` (the client's real address) and a request id for tracing (lesson 36).

The price is CPU and latency for parsing and TLS, and the balancer must understand every protocol it routes. NGINX, HAProxy, Envoy, and AWS's Application Load Balancer are L7 balancers. A common pattern combines them: a tier of L4 balancers spreads connections across a fleet of L7 proxies, which route individual requests.

## Algorithms

Every algorithm answers one question: which healthy backend gets the next request?

### Round robin

Take turns: A, B, C, A, B, C. It's simple, stateless apart from a counter, and perfectly fair *if every request costs the same and every server is equally fast*. Neither is usually true.

### Weighted round robin

Give bigger servers bigger weights. With weights A=5, B=1, C=1, A gets 5 of every 7 requests. A naive version sends A five in a row, then B, then C: a burst that briefly overloads A. NGINX's **smooth weighted round robin** interleaves them instead:

1. Every server keeps a running score, starting at 0.
2. On each pick, add each server's weight to its score.
3. Choose the server with the highest score (ties go to the first), then subtract the total weight from its score.

For A=5, B=1, C=1, that yields A, A, B, A, C, A, A: the same proportions, spread evenly.

### Least connections

Send each request to the backend with the **fewest active requests**. This adapts automatically to real conditions:

- Requests vary in cost: a search takes 500 ms and a profile fetch 5 ms.
- Servers vary in speed: one has a noisy neighbor, a cold cache, or a long garbage collection pause.

Round robin keeps sending a slow server its full share, so requests pile up there and the tail latency explodes (remember queueing, lesson 1). Least connections notices the pile-up, because a slow server's requests stay active longer, and steers around it. The cost is state: the balancer must count active requests per backend, which is easy in one process and hard to share across many balancer instances.

Variants weigh in response time (**least response time**, or an **EWMA**, an exponentially weighted moving average of latency, as used by Linkerd and Envoy).

### Power of two choices

With many load balancers each tracking load separately, or with load information that's a little stale, "always pick the least loaded" backfires: every balancer sees the same idle server and sends its next requests there at once, a **herd**. The fix is surprisingly simple: **sample two backends at random and pick the less loaded of the two**. It's nearly as good as checking every server. Mathematically, the maximum load drops exponentially compared with picking one at random. And because different balancers sample different pairs, they don't stampede the same target. Envoy, NGINX, and HAProxy all offer it.

### Hashing for affinity

Sometimes you *want* the same key on the same backend: a cache server that already holds a user's data, or a shard that owns a partition. Hash a request attribute (user id, URL) to pick the backend. Plain `hash % N` reshuffles almost everything when N changes, so balancers use **consistent hashing** (ring hash, Maglev hashing), which you'll build in lesson 23.

| Algorithm | Needs state? | Handles uneven requests? | Notes |
|---|---|---|---|
| Round robin | A counter | No | Fine for uniform, cheap requests |
| Weighted round robin | Counters | No | For servers of different sizes |
| Least connections | Active counts | Yes | The usual default for L7 |
| Power of two choices | Active counts | Yes | Scales to many balancers |
| Consistent hashing | The ring | No | When a key should stick to a server |

## Health checking

A load balancer is only as good as its knowledge of which backends are alive.

- **Active health checks**: probe each backend periodically, such as `GET /healthz` every 5 seconds. Mark it down after several consecutive failures (say 3) and up again after several successes (say 2). Requiring a streak avoids **flapping** on one lost packet.
- **Passive health checks** (outlier detection): watch real traffic. If a backend returns errors or times out several times in a row, eject it. This reacts to failures between probes, and catches backends that pass `/healthz` but fail real requests.
- **What should `/healthz` check?** If it checks a shared dependency like the database, a database blip makes *every* backend report unhealthy, and the balancer ejects the whole pool, turning a partial outage into a total one. Health checks should mostly report whether *this process* can serve.
- **Connection draining**: before removing a backend for a deploy, stop sending it new requests and let in-flight ones finish.
- **Slow start**: a freshly started backend has cold caches and an unwarmed runtime. Ramp its share of traffic up gradually instead of handing it a full share at once.

Detecting failure always involves a timeout, and a timeout can't distinguish a dead server from a slow one or a lost network path (lesson 27). Every health check is a guess.

## The load balancer is a single point of failure too

Putting one load balancer in front of your servers moves the single point of failure from the servers to the load balancer. Production setups remove it:

- **Active-passive pairs** share a **floating IP** (with a protocol like VRRP). When the active one dies, the standby claims the address within seconds.
- **Active-active fleets** behind anycast or ECMP routing, with many balancers handling traffic at once.
- **Managed cloud load balancers**, which are fleets like this behind the scenes.

## Reverse proxies

A **forward proxy** acts on behalf of *clients* (a corporate proxy that filters outbound browsing). A **reverse proxy** acts on behalf of *servers*: clients think they're talking to the origin, but the proxy receives every request and forwards it. Every L7 load balancer is a reverse proxy, and reverse proxies do much more than balance:

- **TLS termination**: decrypt once at the edge, and manage certificates in one place (next lesson).
- **Buffering slow clients**: a mobile client uploading at 50 KB/s would tie up an application worker for seconds. The proxy absorbs the slow upload and hands the backend a complete request in one burst. This also blunts slow-request attacks like Slowloris.
- **Compression and caching** of responses (lesson 21).
- **Protection**: request size limits, header normalization, and hiding the internal topology.

## API gateways

An **API gateway** is a reverse proxy specialized for the front door of an API, typically one built from many services. It handles cross-cutting concerns once, at the edge, so individual services don't each reimplement them:

- **Routing**: `/api/users/*` to the user service, `/api/orders/*` to the order service. Clients see one API, while the backend is many services that can be split, merged, or moved.
- **Authentication**: verify API keys or tokens (such as JWTs) once, and pass the verified identity to services in a header. The next lesson builds exactly this.
- **Rate limiting and quotas** per client (lesson 22), rejecting floods before they reach anything expensive.
- **Transformation**: translate between protocols (REST outside, gRPC inside), version APIs, and reshape responses.
- **Aggregation**: one client call fans out to several services and returns a combined result. A **backend for frontend (BFF)** is a gateway tailored to one client, such as the mobile app.
- **Observability**: every request passes through, so the gateway is the natural place to record metrics, assign request ids, and start traces (lesson 36).
- **Traffic shifting**: send 1% of traffic to a new version (a **canary**) and watch its error rate before going further.

Gateways have failure modes of their own. Everything flows through them, so they must be highly available and fast. And the temptation to put business logic in the gateway turns it into a distributed monolith that every team must change. Keep it to cross-cutting concerns. For traffic *between* internal services (east-west, as opposed to north-south traffic from clients), a **service mesh** runs a small proxy (often Envoy) beside every service instance and applies the same features without a central gateway (lesson 32).

## Your task

`solution.py` builds the decision-making core of a load balancer and a gateway. There's no network: each `pick()` returns the name of the backend for the next request, and `release(server)` reports that a request to it finished.

### 1. Passive health checks

In the `Balancer` base class, which every algorithm shares:

- `report(server, ok)`: a request succeeded or failed. After `max_failures` failures **in a row**, take the server out of rotation. A success resets its count.
- `mark_up(server)`: an active health check passed. Put the server back, with a fresh failure count.
- `healthy()`: the servers in rotation, in their original order. `pick()` already raises `NoHealthyServers` when there are none, and passes the healthy list to `choose(candidates)`.

### 2. Algorithms

Implement `choose(candidates)` for:

- `WeightedRoundRobin`: the smooth algorithm above. For weights 5, 1, 1 the tests expect A, A, B, A, C, A, A.
- `LeastConnections`: the candidate with the fewest active requests (`self.active[server]`), ties going to the first in the list. Count the request as active, and implement `release(server)`.
- `PowerOfTwoChoices`: `self.rng.sample(candidates, 2)`, then the less busy of the two (the first sampled on a tie). With one healthy server, use it.

A test replays a stream of requests against two fast servers and one slow one. Round robin averages about 40 ticks per request, and your least connections must beat 20.

### 3. A gateway

`Gateway(routes, api_keys).handle(path, headers)` returns `(status, server)`:

- `(401, None)` unless the `Authorization` header is `Bearer <key>` with a valid key.
- Route by the **longest** matching prefix, matching whole path segments only: `/api/users` matches `/api/users` and `/api/users/42`, but not `/api/usersettings`. No match is `(404, None)`.
- `(200, server)` from the route's balancer, or `(503, None)` if it has no healthy servers.

Afterward, go back to lesson 7's canvas, double-click the load balancer, and switch it to **least connections**. Then make one server slow (give it fewer connections) and compare.

## Key terms

| Term | Meaning |
|---|---|
| L4 load balancer | Forwards TCP/UDP connections without reading their contents |
| L7 load balancer | Terminates HTTP and routes each request by its contents |
| Sticky session | Routing a client back to the same server every time |
| Least connections | Choose the backend with the fewest active requests |
| Power of two choices | Sample two backends and take the less loaded |
| Active / passive health check | Probing backends / watching real traffic for failures |
| Connection draining | Letting in-flight requests finish before removing a backend |
| Reverse proxy | A server that receives requests on behalf of backends |
| API gateway | A reverse proxy handling auth, routing, and limits for an API |
| Service mesh | Per-service proxies handling traffic between internal services |
