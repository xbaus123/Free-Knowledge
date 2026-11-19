# Cache Keys, Invalidation, and What to Cache

*Chapter 6 · Partitioning and Geography.*

## Cache keys

A CDN stores each response under a **cache key**, by default the host, path, and query string. Every distinct key is a separate cache entry, so careless keys destroy the hit ratio:

- **Query strings**: `?a=1&b=2` and `?b=2&a=1` are the same page. Sort parameters, and drop ones that don't affect the response, like the `utm_*` tracking tags marketing adds to every link.
- **`Vary`**: a response with `Vary: Accept-Language` must be stored separately for each language, so the header's value becomes part of the key. `Vary: User-Agent` is a disaster: there are thousands of distinct user-agent strings, so the cache holds thousands of copies and rarely hits. `Vary: *` means the response can't be reused at all.
- **Normalization**: browsers send `Accept-Encoding: gzip, deflate, br` in dozens of spellings. The edge serves only two or three encodings, so it collapses the header to the one it will use before adding it to the key.

## Invalidation

There are two hard problems in computer science, and cache invalidation at 300 PoPs is one of them.

- **Expiry (TTL)**: simple and reliable, but content stays stale until it expires.
- **Purge**: tell the CDN to drop a URL now. It takes seconds to reach every PoP, and you must know every URL the change affected.
- **Surrogate keys** (cache tags): the origin labels responses with tags like `product-42`, and one purge of the tag drops every page that showed product 42.
- **Versioned URLs**: the best invalidation is none at all. Build tools put a hash of the content in each static file's name (`app.3f9a1c.js`) and serve it with `max-age=31536000, immutable`. A changed file gets a new name, the HTML references the new name, and the old file simply stops being requested. Only the HTML needs a short TTL.

## Tiered caching and request collapsing

With 300 PoPs each missing independently, a new object causes 300 requests to the origin. **Tiered caching** puts a few regional mid-tier caches (an **origin shield**) between the edges and the origin, so edges miss to the shield and the origin sees roughly one request per object. **Request collapsing** handles the thundering herd you met in chapter 5: when 1,000 requests for the same missing object arrive at once, the CDN forwards one to the origin and makes the other 999 wait for its response.

## Static versus dynamic content

| Content | Example | CDN strategy |
|---|---|---|
| **Versioned static assets** | `app.3f9a1c.js`, product images | Cache for a year, `immutable`; never purge |
| **Unversioned static content** | `/logo.png`, `/robots.txt` | Moderate TTL, purge on change |
| **Shared dynamic pages** | News front page, product page, search results for popular queries | **Microcache**: 1 to 10 seconds. At 5,000 requests per second, a 1-second TTL turns 5,000 origin requests into about 1 per PoP |
| **Personalized pages** | Your feed, your cart | Not cached, but still accelerated: TLS at the edge, warm backbone connections. Cache the shared fragments and assemble them at the edge |
| **APIs** | `GET /api/products/42` | Cache public `GET`s briefly with `s-maxage`; never cache anything per user without the user in the key |
| **Video** | HLS/DASH streams | Split into small segment files that cache like static assets |

**Edge compute** (Cloudflare Workers, Lambda@Edge, Fastly Compute) runs your code in the PoPs themselves: checking a JWT (chapter 2) before a request ever reaches the origin, choosing an A/B test variant, rewriting URLs, or assembling a page from cached fragments with one personalized piece. It's the logical end of the CDN's evolution: from caching files, to caching pages, to running part of the application at the edge.

Next, a short check on what you just read.
