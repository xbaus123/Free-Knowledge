# Power of Two Choices and Hashing

*Chapter 2 · The Front Door.*

## Power of two choices

With many load balancers each tracking load separately, or with load information that's a little stale, "always pick the least loaded" backfires: every balancer sees the same idle server and sends its next requests there at once, a **herd**. The fix is surprisingly simple: **sample two backends at random and pick the less loaded of the two**. It's nearly as good as checking every server. Mathematically, the maximum load drops exponentially compared with picking one at random. And because different balancers sample different pairs, they don't stampede the same target. Envoy, NGINX, and HAProxy all offer it.

## Hashing for affinity

Sometimes you *want* the same key on the same backend: a cache server that already holds a user's data, or a shard that owns a partition. Hash a request attribute (user id, URL) to pick the backend. Plain `hash % N` reshuffles almost everything when N changes, so balancers use **consistent hashing** (ring hash, Maglev hashing), which you'll build in chapter 6.

| Algorithm | Needs state? | Handles uneven requests? | Notes |
|---|---|---|---|
| Round robin | A counter | No | Fine for uniform, cheap requests |
| Weighted round robin | Counters | No | For servers of different sizes |
| Least connections | Active counts | Yes | The usual default for L7 |
| Power of two choices | Active counts | Yes | Scales to many balancers |
| Consistent hashing | The ring | No | When a key should stick to a server |

Next, a short check on what you just read.
