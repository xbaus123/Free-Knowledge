# Rate Limiting

*Chapter 6 · Partitioning and Geography.*

## Rate limiting

Partitioning protects you from *expected* growth. **Rate limiting** protects you from the unexpected: a buggy client in a retry loop, a scraper, or an attacker. It caps how many requests a client (by API key, user, or IP address) may send, and rejects the excess with `429 Too Many Requests`, ideally with a `Retry-After` header.

| Algorithm | How it works | Trade-off |
|---|---|---|
| **Token bucket** | Each client has a bucket of up to B tokens, refilled at R per second. Each request spends one. | Allows short bursts up to B while capping the average rate at R. The most common choice. |
| **Leaky bucket** | Requests join a queue drained at a fixed rate. | Smooth output, but bursts wait or are dropped. |
| **Fixed window** | Count requests per calendar minute. | Simple, but a client can send 2× the limit across a window boundary. |
| **Sliding window** | Weight the previous window's count by how much of it overlaps. | Smooths the boundary problem cheaply. |

With many API servers, the counters must be **shared**, usually in Redis with atomic increments, or kept approximately per server. Put limits early (at the edge or in an API gateway, chapter 2) so rejected requests cost almost nothing. Set them high enough that real users never notice. The simulator's capstone counts real users rejected by an overeager limiter as failures.

## Key terms

| Term | Meaning |
|---|---|
| Partition / shard | A subset of the data on one node (or replica set) |
| Skew / hot spot | Uneven load / one overloaded partition |
| Key-range partitioning | Contiguous key ranges per partition; good for scans |
| Hash partitioning | Ranges of key hashes per partition; even, but no scans |
| Consistent hashing | A hash ring where adding a node moves about 1/N of the keys |
| Scatter/gather | Querying every partition and combining the results |
| Token bucket | Rate limiting with a refilling allowance of requests |

Next, a short check on what you just read.
