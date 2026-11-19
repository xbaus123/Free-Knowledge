# Geographical Distribution: Multi-Region, Anycast, and CDNs

*Chapter 6 · Partitioning and Geography.*

Build what the geography readings described: global traffic routing with residency rules, active-active CRDT counters, and CDN caching rules.

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
