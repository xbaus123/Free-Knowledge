# Health Checks and Redundant Balancers

*Chapter 2 · The Front Door.*

## Health checking

A load balancer is only as good as its knowledge of which backends are alive.

- **Active health checks**: probe each backend periodically, such as `GET /healthz` every 5 seconds. Mark it down after several consecutive failures (say 3) and up again after several successes (say 2). Requiring a streak avoids **flapping** on one lost packet.
- **Passive health checks** (outlier detection): watch real traffic. If a backend returns errors or times out several times in a row, eject it. This reacts to failures between probes, and catches backends that pass `/healthz` but fail real requests.
- **What should `/healthz` check?** If it checks a shared dependency like the database, a database blip makes *every* backend report unhealthy, and the balancer ejects the whole pool, turning a partial outage into a total one. Health checks should mostly report whether *this process* can serve.
- **Connection draining**: before removing a backend for a deploy, stop sending it new requests and let in-flight ones finish.
- **Slow start**: a freshly started backend has cold caches and an unwarmed runtime. Ramp its share of traffic up gradually instead of handing it a full share at once.

Detecting failure always involves a timeout, and a timeout can't distinguish a dead server from a slow one or a lost network path (chapter 7). Every health check is a guess.

## The load balancer is a single point of failure too

Putting one load balancer in front of your servers moves the single point of failure from the servers to the load balancer. Production setups remove it:

- **Active-passive pairs** share a **floating IP** (with a protocol like VRRP). When the active one dies, the standby claims the address within seconds.
- **Active-active fleets** behind anycast or ECMP routing, with many balancers handling traffic at once.
- **Managed cloud load balancers**, which are fleets like this behind the scenes.

Next, a short check on what you just read.
