# Load Balancing, Reverse Proxies, and API Gateways

*Chapter 2 · The Front Door.*

Build the decision-making core of a load balancer and a gateway from the last five readings: passive health checks, three algorithms, and prefix routing.

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

Afterward, go back to the scaling-out lab's canvas, double-click the load balancer, and switch it to **least connections**. Then make one server slow (give it fewer connections) and compare.

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
