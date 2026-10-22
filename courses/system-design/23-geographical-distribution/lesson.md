# Geographical Distribution: Multi-Region, Anycast, and CDNs

*Based on* Designing Data-Intensive Applications*, Chapters 5 and 6.*

Everything you've built so far lives in one data center. Replicas protect you from a failed disk or machine, and partitions spread load across racks. But the whole system still shares one building, one power grid, one network provider, and one spot on the map. This lesson spreads it across the planet: running in several regions at once, steering each user to the right one, keeping their data where the law says it must stay, and pushing content to the edge of the network with a CDN.

## Why go multi-region

Three forces push a system out of a single region.

**Latency.** Light in optical fiber travels about 200,000 km per second, roughly 200 km per millisecond. New York to London is about 5,600 km, so the round trip can't be faster than 56 ms, and in practice it's about 70. Sydney to Virginia is closer to 200 ms. Lesson 2 showed that opening an HTTPS connection costs several round trips before the first byte arrives, so a user on the far side of the world waits most of a second for a page that a nearby user gets in 100 ms. No amount of server capacity fixes the speed of light. Only moving the servers closer does.

**Availability.** Whole regions fail: a power event, a cooling failure, a bad configuration push to a regional control plane, a fiber cut. Every major cloud has had multi-hour regional outages. If your only region goes down, so do you, however many replicas you have inside it.

**Regulation.** Many jurisdictions restrict where personal data may be stored and processed. Some customers, especially governments, banks, and hospitals, require it contractually. You can't serve them from a single region on another continent.

The costs are real too: more infrastructure (each region needs enough capacity to be useful), cross-region bandwidth bills, much harder data consistency, and deploys and incidents that span time zones.

## Disaster recovery vocabulary

Two numbers describe what a regional failure costs you:

- **RPO** (recovery point objective): how much recently written data you can afford to lose. With asynchronous replication to another region, it's the replication lag, typically seconds.
- **RTO** (recovery time objective): how long until you're serving again in another region. It ranges from hours (restore from backups) to seconds (traffic is already flowing there).

## Multi-region topologies

From simplest to most ambitious:

| Topology | Writes go to | Reads served | On region loss | Hard part |
|---|---|---|---|---|
| **Single region + CDN** | The one region | Static content at the edge; the rest from the region | Down | Distant users wait on every dynamic request |
| **Active-passive** (warm standby) | The primary region | The primary region | Promote the standby: RPO = lag, RTO = minutes | Standby capacity sits idle; failover is rarely exercised, so it often doesn't work |
| **Read local, write global** | One leader region | Every region, from local followers | Promote a follower in another region | Writes from far away are slow; reads may be stale |
| **Geo-partitioned** (home region per user) | Each user's home region | The home region, or anywhere if slightly stale is fine | That region's users fail over or wait | Users who move, and data shared between users in different regions |
| **Multi-leader** (active-active) | Any region | Any region | Others keep going | **Write conflicts** |
| **Globally consensus-replicated** | A leader per partition, agreed by quorum across regions | Any region, with a consistency choice | A quorum survives the loss of one region | Every write waits for a cross-region round trip |

### Read local, write global

The single-leader replication of lesson 18, stretched across regions. The leader sits in one region, and every region has followers. Reads are fast everywhere, and writes travel to the leader. It works well for read-heavy workloads, but the replication-lag anomalies you saw in lesson 19 grow from milliseconds to hundreds of milliseconds. A user who writes in Sydney and reads back from the Sydney follower may not see their own write, so route a user's reads to the leader for a few seconds after they write (**read-your-writes**).

### Geo-partitioning

Give every user a **home region**, and keep their data there. A European user's profile, orders, and messages live in Frankfurt, and all writes for them go to Frankfurt. This is partitioning (lesson 21) with geography as the partition key. It avoids write conflicts entirely, because each record has exactly one leader, and it's the natural way to satisfy data residency rules. CockroachDB's `REGIONAL BY ROW` tables and Spanner's placement rules do this at the database level. The trouble is data that doesn't belong to one user: a group chat with members on three continents, or a global product catalog. Those need a home too, or one of the other topologies.

### Multi-leader active-active

Every region accepts writes and replicates them asynchronously to the others. DDIA calls this **multi-leader replication** and notes that multiple data centers are its main use case. Each region tolerates the loss of the others and keeps writes fast. But two regions can accept conflicting writes to the same record at the same time, and neither knows until replication delivers the other's version. Something must **resolve the conflict**:

- **Last write wins (LWW)**: keep the write with the latest timestamp. It's simple, and it silently **discards** data: two people liking a post at the same time in two regions, each writing `likes = 101`, leaves 101, not 102. And it trusts timestamps from clocks that disagree (lesson 26).
- **Conflict-free replicated data types (CRDTs)**: data structures whose replicas can be updated independently and **merged** in any order, any number of times, always converging to the same result. You'll build one below.
- **Application-level merge**: keep every conflicting version (as **siblings**) and let application code or the user combine them, as a shopping cart might take the union of items.

Cassandra and DynamoDB global tables run active-active across regions. Cassandra lets each request choose `LOCAL_QUORUM` (a quorum of replicas in the local region: fast, but another region may briefly disagree) or `EACH_QUORUM` (a quorum in every region: consistent, but as slow as the farthest one).

### Global consensus

Google Spanner and CockroachDB run consensus (lesson 28) for each partition, with replicas in several regions. A write commits once a majority has it, so losing one region loses nothing, and reads can be linearizable. The cost is physics: every write waits for a round trip to the nearest majority. With replicas in Virginia, Oregon, and Iowa, that's tens of milliseconds. Spanner goes further and uses its **TrueTime** clock API, backed by GPS receivers and atomic clocks, to give transactions globally meaningful timestamps.

This is the latency half of the **PACELC** trade-off: even when there's no network partition (the "else" case), a geo-distributed system chooses between low latency and strong consistency. Most designs choose differently for different data. A bank balance gets consensus. A like count gets a CRDT.

### CRDT counters

A counter shows the CRDT idea clearly. Instead of storing one number, each replica stores **one number per region**: how many increments that region has made. A region only ever increments its own entry. To merge another replica's state, take the **maximum** of each entry. The value is the sum of the entries.

```text
us-east: {us: 5, eu: 0}   +   eu-west: {us: 0, eu: 3}   →   merged: {us: 5, eu: 3} = 8
```

Taking the maximum makes merging **commutative** (order doesn't matter), **associative** (grouping doesn't matter), and **idempotent** (merging the same state twice changes nothing). That's exactly what you need over an unreliable network that delays, reorders, and duplicates messages. Increments are never lost, because each region's entry only grows. To support decrements, keep a second map of decrements, a **PN-counter** (positive-negative). The same idea, a state that only grows under a merge, gives sets, registers, maps, and even collaborative text editing.

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

The large clouds and CDNs combine both. Anycast brings the user's TCP and TLS handshakes to a **point of presence (PoP)** a few milliseconds away. The PoP then forwards the request to the right region over the provider's private backbone, on connections that are already open and warmed up. Lesson 2's handshake round trips now cross 10 ms instead of 150, even for requests that can't be cached.

### Capacity and failover

A GSLB balances on health and capacity, not just distance: it sends users to the nearest healthy region that has room, and **spills over** to the next nearest when it doesn't. Plan capacity at the region level as you did for servers: with three regions each running at 70%, losing one sends its traffic to the other two, pushing them to 105%. A region failure then becomes a global overload. Either keep each region below about 60%, or have a plan for **load shedding** (deliberately rejecting low-priority work). Exercise failover regularly. A failover path that's never used is a failover path that doesn't work.

## Data sovereignty and residency

- **Data residency**: *where* data is physically stored and processed.
- **Data sovereignty**: *whose laws* apply to it. Data stored in Frankfurt by an American company may still be subject to American legal demands, which is why some customers insist on providers headquartered locally.

The European Union's **GDPR** restricts transferring personal data outside the EU unless the destination offers equivalent protection. China, India, Russia, and others have localization laws of their own, and industries like healthcare and finance add more rules. The design consequences:

- **Partition by jurisdiction.** Give each user a home region in their jurisdiction, and keep their personal data there. Global services handle only pseudonymous ids.
- **Everything is data.** Logs, backups, analytics pipelines, search indexes, caches, error reports, and the support team's admin tools all copy data. A residency guarantee has to cover every one of them.
- **Fail closed.** If both EU regions are down, the router must refuse an EU user's request rather than quietly sending it to Virginia. A residency rule that a failover can violate isn't a rule. If you need regional failover, provision two regions *inside* the jurisdiction.
- **Encrypt with regional keys.** Keep encryption keys in a key management service in the same jurisdiction. Destroying a key makes every copy of the data unreadable, even in backups (**crypto-shredding**).

## CDNs in depth

A **content delivery network** is a fleet of caching reverse proxies (lesson 8) in hundreds of PoPs around the world. Lesson 19's simulator had one as a single box. In reality, a CDN does four jobs:

1. **Caches** content close to users, so most requests never cross an ocean.
2. **Offloads** the origin: a 95% hit ratio means the origin serves 1 request in 20.
3. **Terminates TCP and TLS** near the user, and keeps warm connections to the origin.
4. **Absorbs attacks**: DDoS traffic lands on the CDN's enormous edge capacity, not your servers.

### What a CDN may cache

A CDN is a **shared cache**: one stored response is served to many users. The origin controls it with the `Cache-Control` header (RFC 9111):

| Directive | Meaning for a shared cache |
|---|---|
| `max-age=N` | Fresh for N seconds |
| `s-maxage=N` | Fresh for N seconds in *shared* caches only; overrides `max-age` there |
| `public` | May be stored, even for a request with an `Authorization` header |
| `private` | Only the user's own browser may store it; never a CDN |
| `no-store` | Nobody stores it at all |
| `no-cache` | May be stored, but must be revalidated with the origin before every use |
| `immutable` | Will never change while fresh; don't bother revalidating |
| `stale-while-revalidate=N` | After expiry, serve the stale copy for up to N seconds while fetching a fresh one in the background |
| `stale-if-error=N` | If the origin is failing, serve the stale copy for up to N seconds |

Two more safety rules matter in practice. A response that sets a cookie (`Set-Cookie`) is almost certainly personal, so CDNs don't cache it by default. And a request carrying an `Authorization` header is for a specific user, so a shared cache may only store the response if the origin says so explicitly (`public` or `s-maxage`). Getting these wrong is how one user's account page ends up served to thousands of strangers, a real incident that has happened to large companies.

`stale-if-error` deserves attention in a multi-region design: when an origin region fails, the CDN can keep serving the last good copy of pages and assets, hiding the outage from many users.

### Cache keys

A CDN stores each response under a **cache key**, by default the host, path, and query string. Every distinct key is a separate cache entry, so careless keys destroy the hit ratio:

- **Query strings**: `?a=1&b=2` and `?b=2&a=1` are the same page. Sort parameters, and drop ones that don't affect the response, like the `utm_*` tracking tags marketing adds to every link.
- **`Vary`**: a response with `Vary: Accept-Language` must be stored separately for each language, so the header's value becomes part of the key. `Vary: User-Agent` is a disaster: there are thousands of distinct user-agent strings, so the cache holds thousands of copies and rarely hits. `Vary: *` means the response can't be reused at all.
- **Normalization**: browsers send `Accept-Encoding: gzip, deflate, br` in dozens of spellings. The edge serves only two or three encodings, so it collapses the header to the one it will use before adding it to the key.

### Invalidation

There are two hard problems in computer science, and cache invalidation at 300 PoPs is one of them.

- **Expiry (TTL)**: simple and reliable, but content stays stale until it expires.
- **Purge**: tell the CDN to drop a URL now. It takes seconds to reach every PoP, and you must know every URL the change affected.
- **Surrogate keys** (cache tags): the origin labels responses with tags like `product-42`, and one purge of the tag drops every page that showed product 42.
- **Versioned URLs**: the best invalidation is none at all. Build tools put a hash of the content in each static file's name (`app.3f9a1c.js`) and serve it with `max-age=31536000, immutable`. A changed file gets a new name, the HTML references the new name, and the old file simply stops being requested. Only the HTML needs a short TTL.

### Tiered caching and request collapsing

With 300 PoPs each missing independently, a new object causes 300 requests to the origin. **Tiered caching** puts a few regional mid-tier caches (an **origin shield**) between the edges and the origin, so edges miss to the shield and the origin sees roughly one request per object. **Request collapsing** handles the thundering herd you met in lesson 20: when 1,000 requests for the same missing object arrive at once, the CDN forwards one to the origin and makes the other 999 wait for its response.

### Static versus dynamic content

| Content | Example | CDN strategy |
|---|---|---|
| **Versioned static assets** | `app.3f9a1c.js`, product images | Cache for a year, `immutable`; never purge |
| **Unversioned static content** | `/logo.png`, `/robots.txt` | Moderate TTL, purge on change |
| **Shared dynamic pages** | News front page, product page, search results for popular queries | **Microcache**: 1 to 10 seconds. At 5,000 requests per second, a 1-second TTL turns 5,000 origin requests into about 1 per PoP |
| **Personalized pages** | Your feed, your cart | Not cached, but still accelerated: TLS at the edge, warm backbone connections. Cache the shared fragments and assemble them at the edge |
| **APIs** | `GET /api/products/42` | Cache public `GET`s briefly with `s-maxage`; never cache anything per user without the user in the key |
| **Video** | HLS/DASH streams | Split into small segment files that cache like static assets |

**Edge compute** (Cloudflare Workers, Lambda@Edge, Fastly Compute) runs your code in the PoPs themselves: checking a JWT (lesson 9) before a request ever reaches the origin, choosing an A/B test variant, rewriting URLs, or assembling a page from cached fragments with one personalized piece. It's the logical end of the CDN's evolution: from caching files, to caching pages, to running part of the application at the edge.

## Your task

`solution.py` has three parts. `distance_km` (the great-circle distance between two points), `cache_control` (a `Cache-Control` parser), `lower_keys`, and `normalize_encoding` are done.

### 1. Global traffic routing

`GlobalRouter(regions, residency)` steers users to regions. `regions` maps each region's name to its `location` (latitude, longitude), `jurisdiction`, and `capacity` (active requests it can handle). `residency` maps a jurisdiction to the set of jurisdictions its users' data may be processed in; users from a jurisdiction not listed can go anywhere. `mark_down`, `mark_up`, and `finish` are done.

- `candidates(location, jurisdiction)`: the names of regions that are **up** and **allowed** for this user, sorted by distance from `location` (ties by name).
- `route(location, jurisdiction)`: raise `NoRegion` if there are no candidates. Otherwise pick the nearest candidate whose `self.load` is below its capacity. If every one is full, pick the nearest anyway. Add 1 to the chosen region's load and return its name.

### 2. Active-active counters

`PNCounter(region)` is a replica of a counter living in `region`. `self.incs` and `self.decs` map each region to the total increments and decrements made there.

- `increment(n=1)` and `decrement(n=1)` change only this replica's own region's entries.
- `value()` is the total increments minus the total decrements.
- `merge(other)` takes, for every region in either replica, the maximum of the two entries, for both maps. Merging must be safe to repeat and to do in any order.

### 3. CDN caching rules

`edge_ttl(request_headers, status, response_headers)` returns how many seconds a CDN may cache the response, or 0. Header names are case-insensitive.

- Only statuses 200, 301, 404, and 410 are cacheable.
- Never cache a response with `Set-Cookie`, or with `no-store`, `private`, or `no-cache`.
- If the request has an `Authorization` header, cache only if the response has `public` or `s-maxage`.
- Use `s-maxage` if present, else `max-age`. Without either, or if the value isn't an integer, return 0.

`cache_key(url, request_headers, vary=())` returns the key to store the response under:

- `None` if any `vary` entry is `*`.
- Otherwise `host + path`, with the host lowercased and an empty path as `/`.
- Then, if any query parameters remain after dropping those that start with an entry of `IGNORED_PARAMS`, add `?` and the parameters **sorted**, re-encoded with `urlencode`. (`urlsplit` and `parse_qsl` are imported for you.)
- Then, for each `vary` header name, lowercased and in sorted order, add `|name=value` with the request's value of that header (empty if missing). For `accept-encoding`, use `normalize_encoding(value)` instead.

For example, `cache_key("https://CDN.Example.com/a?w=2&f=webp", {"Accept-Language": "fr"}, ["Accept-Language"])` is `"cdn.example.com/a?f=webp&w=2|accept-language=fr"`.

Try the router in the **Scratchpad**:

```python
from solution import GlobalRouter

regions = {
    "us-east": {"location": (39.0, -77.5), "jurisdiction": "US", "capacity": 10},
    "eu-west": {"location": (53.3, -6.3), "jurisdiction": "EU", "capacity": 10},
}
r = GlobalRouter(regions, {"EU": {"EU"}})
print(r.route((48.9, 2.35), "EU"), r.route((40.7, -74.0), "EU"))
```

## Think about it

- Your PN-counter keeps one entry per region. What would go wrong if every *user* got their own entry instead, and what would you do about it?
- A user's home region is Frankfurt, and they move to Singapore. What has to happen to their data, and what does the user experience while it does?
- The front page of a news site is the same for everyone except a "Hi, Sam" in the corner. How would you get it served from the edge anyway?

## Key terms

| Term | Meaning |
|---|---|
| Region / PoP | A cloud location with full data centers / a small edge site for caching and connection termination |
| RPO / RTO | Data you can lose / time until you're back, after a failure |
| Active-passive / active-active | One region serves while another waits / several regions serve at once |
| Geo-partitioning | Keeping each user's data in a home region |
| Multi-leader replication | Several regions accept writes and replicate them to each other |
| CRDT | A data type whose replicas merge in any order to the same result |
| PN-counter | A CRDT counter: per-region increments and decrements, merged by maximum |
| GSLB | Global server load balancing: choosing a region for each user |
| GeoDNS | DNS answers that depend on where the query came from |
| Anycast | Many locations announcing the same IP, so routing picks the nearest |
| Data residency / sovereignty | Where data is stored / whose laws govern it |
| Shared cache | A cache, like a CDN, that serves one stored response to many users |
| `s-maxage` | A freshness lifetime for shared caches only |
| Surrogate key | A tag on cached responses, for purging related pages at once |
| Origin shield | A mid-tier cache between edge PoPs and the origin |
| Microcaching | Caching dynamic content for a second or a few |
