# Where Balancing Happens: DNS, L4, L7

*Chapter 2 · The Front Door.*

## Where balancing happens

Load can be spread at several layers, and big systems use most of them at once:

| Layer | How | Strengths | Weaknesses |
|---|---|---|---|
| **DNS** | Return different IP addresses for one name (chapter 1) | Free, global, works across regions | Clients and resolvers cache answers, so changes and failover lag by the TTL; no knowledge of load |
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
- **retry** a failed request on another backend (only when it's idempotent; chapter 1),
- add headers such as `X-Forwarded-For` (the client's real address) and a request id for tracing (chapter 10).

The price is CPU and latency for parsing and TLS, and the balancer must understand every protocol it routes. NGINX, HAProxy, Envoy, and AWS's Application Load Balancer are L7 balancers. A common pattern combines them: a tier of L4 balancers spreads connections across a fleet of L7 proxies, which route individual requests.

Next, a short check on what you just read.
