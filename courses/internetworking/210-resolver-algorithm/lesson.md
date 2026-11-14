# The Resolver Algorithm

*Chapter 7 · DNS.*

Here's how a recursive resolver turns a question into an answer. It's a short loop.

## The algorithm

1. **Check the cache.** If the answer (or a cached error, like "no such name") is there, return it to the client. Done.
2. **Find the best servers to ask.** Look for the closest known ancestor of SNAME: cached NS records for `marshall.edu` beat those for `edu`, which beat the root (from SBELT). Put them in SLIST.
3. **Send queries** to servers in SLIST until one responds.
4. **Read the response:**
   - **An answer, or an error** saying the name doesn't exist: **cache it** and reply to the client.
   - **A referral** to another part of the tree ("I don't know, but ask these servers for `marshall.edu`"): **cache the delegation** and go back to **step 2**.
   - **A CNAME** that isn't what was asked for: **cache it**, change SNAME to the canonical name, and **start again** with the new name.
   - **A server failure, or nonsense**: **remove that server from SLIST** and go back to step 3.

## Walking the tree

With an empty cache, looking up `example.net`:

```
Client ──"example.net?"──▶ Recursive resolver
                             │ 1 ──"example.net?"──▶ Root server
                             │ ◀── "ask the .net servers"
                             │ 2 ──"example.net?"──▶ .net TLD server
                             │ ◀── "ask example.net's servers"
                             │ 3 ──"example.net?"──▶ Authoritative server
                             │ ◀── "1.2.3.4"
Client ◀────"1.2.3.4"────────┘
```

Two different styles happen here:

- **Recursive**: the client asks once and says "get me the final answer." The resolver does all the work.
- **Iterative**: the resolver asks each server, and each one replies with a **referral** to a server closer to the answer. Root and TLD servers only answer this way.

## Caching makes it fast

The second lookup of `example.net` stops at step 1. A lookup for `other.net` skips the root, because the `.net` delegation is already cached. That's why most lookups take a few milliseconds instead of three round trips, and why the root servers aren't buried in traffic. Each cached record lives until its **TTL** runs out.

Next, a check on the algorithm.
