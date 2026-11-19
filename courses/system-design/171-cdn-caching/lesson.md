# CDNs and What They May Cache

*Chapter 6 · Partitioning and Geography.*

## CDNs in depth

A **content delivery network** is a fleet of caching reverse proxies (chapter 2) in hundreds of PoPs around the world. A CDN does four jobs:

1. **Caches** content close to users, so most requests never cross an ocean.
2. **Offloads** the origin: a 95% hit ratio means the origin serves 1 request in 20.
3. **Terminates TCP and TLS** near the user, and keeps warm connections to the origin.
4. **Absorbs attacks**: DDoS traffic lands on the CDN's enormous edge capacity, not your servers.

## What a CDN may cache

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

Next, a short check on what you just read.
