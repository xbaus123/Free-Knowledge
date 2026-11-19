# REST

*Chapter 1 · Foundations.*

## REST: resources and uniform methods

**REST** (representational state transfer) organizes an API around **resources**, the nouns of your domain, each identified by a URL: `/books`, `/books/8`, `/authors/1/books`. A small, fixed set of **methods** acts on any resource:

| Method | Meaning | Safe? | Idempotent? |
|---|---|---|---|
| `GET` | Read | Yes | Yes |
| `PUT` | Create or replace at this URL | No | Yes |
| `DELETE` | Remove | No | Yes |
| `PATCH` | Partially update | No | Not necessarily |
| `POST` | Create in a collection, or do an action | No | No |

- **Safe** means no side effects: anyone (a crawler, a cache, a prefetching browser) can call it freely.
- **Idempotent** means doing it twice has the same *effect* as doing it once. Deleting book 8 twice leaves book 8 deleted, even though the second call answers `404`. Idempotency matters because of timeouts: if a request times out, you don't know whether it ran, and only an idempotent request is safe to retry blindly.

`POST` isn't idempotent: retry a timed-out "create order" and you might get two orders. The standard fix is an **idempotency key**. The client generates a unique key per logical operation and sends it as a header. The server remembers the response it sent for each key and replays it for a retry instead of acting twice. Stripe's API works this way.

### Pagination

Never return an unbounded list. Two common schemes:

- **Offset**: `?offset=40&limit=20`. Simple, but slow for deep pages (the database still walks past the first 40), and rows shift when items are added or deleted mid-scroll.
- **Cursor**: `?after=137&limit=20`, where the cursor is the last item the client saw. The server answers "items after 137" with an index seek, and inserts elsewhere don't shift the page. The response includes the cursor for the next page, or nothing when there isn't one.

### Why REST dominates public APIs

Its uniformity is the point. Every HTTP client, proxy, and CDN understands `GET` is safe and cacheable, and `curl` is a debugger. The costs: a client that needs a book, its author, and their other books makes several round trips (**under-fetching**), and each response carries every field whether or not the client wants it (**over-fetching**).

Next, a short check on what you just read.
