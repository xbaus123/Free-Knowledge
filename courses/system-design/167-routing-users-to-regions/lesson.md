# Routing Users to Regions

*Chapter 6 · Partitioning and Geography.*

## Routing users to regions

A user types `example.com`. Something must decide which region answers. That's **global server load balancing (GSLB)**, and there are two main techniques.

### GeoDNS

Your authoritative DNS server returns a different IP address depending on where the query comes from: a European IP to European users, an American IP to Americans. It's simple and works anywhere, but:

- DNS sees the **resolver**, not the user. A user in Madrid using a public resolver may look like they're in Amsterdam. The **EDNS Client Subnet** extension passes part of the user's address along to fix this.
- Answers are **cached** for their TTL, and some resolvers and clients ignore short TTLs. Failing over a region by changing DNS takes minutes, and a long tail of clients keeps going to the dead region much longer.

### Anycast

With **anycast**, many locations announce the **same IP address** to the internet through BGP, the protocol routers use to share paths. Each router sends packets along its shortest route, so a user's packets reach whichever location is "closest" in network terms, without DNS doing anything. If a location fails, it **withdraws** its announcement and, within seconds, routers send traffic to the next closest. Cloudflare, Google's front ends, and the public DNS resolvers `1.1.1.1` and `8.8.8.8` all work this way.

- "Closest" means fewest network hops and the routing policies between providers, not kilometers. Usually that's close to geography, but not always.
- Routes can change mid-connection, which would break a long-lived TCP connection. That's rare enough in practice that anycast now carries TCP and TLS, not just DNS.
- Anycast spreads a **DDoS attack** across every location, instead of concentrating it on one.

### Terminate at the edge, ride the backbone

The large clouds and CDNs combine both. Anycast brings the user's TCP and TLS handshakes to a **point of presence (PoP)** a few milliseconds away. The PoP then forwards the request to the right region over the provider's private backbone, on connections that are already open and warmed up. Chapter 1's handshake round trips now cross 10 ms instead of 150, even for requests that can't be cached.

### Capacity and failover

A GSLB balances on health and capacity, not just distance: it sends users to the nearest healthy region that has room, and **spills over** to the next nearest when it doesn't. Plan capacity at the region level as you did for servers: with three regions each running at 70%, losing one sends its traffic to the other two, pushing them to 105%. A region failure then becomes a global overload. Either keep each region below about 60%, or have a plan for **load shedding** (deliberately rejecting low-priority work). Exercise failover regularly. A failover path that's never used is a failover path that doesn't work.

Next, a short check on what you just read.
