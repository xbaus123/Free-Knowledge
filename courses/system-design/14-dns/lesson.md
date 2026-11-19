# DNS: Names to Addresses

*Chapter 1 · Foundations.*

## DNS: names to addresses

People and config files use names like `api.example.com`. The **Domain Name System** turns them into addresses. It's a distributed, hierarchical, heavily cached database:

1. Your machine asks a **recursive resolver** (run by your ISP, your cloud provider, or `8.8.8.8`).
2. If the resolver has nothing cached, it asks a **root server**: "where is `api.example.com`?" The root doesn't know, but it **refers** the resolver to the servers for `com`.
3. The `com` servers refer it to the **authoritative servers** for `example.com`.
4. The authoritative server answers with the record.

Common record types:

| Type | Meaning |
|---|---|
| `A` / `AAAA` | The name's IPv4 / IPv6 address |
| `CNAME` | An alias: "this name is really that name" (look that one up instead) |
| `NS` | Which servers are authoritative for a zone (the referrals above) |
| `MX` | Where to deliver mail for the domain |

Every record carries a **TTL** (time to live, in seconds). Resolvers cache answers *and* referrals until their TTL runs out, which is why most lookups never leave the resolver, and why the root servers aren't buried under the internet's traffic.

TTLs are a design decision:

- **Long TTLs** (hours): fewer lookups, faster responses, but a change (moving to a new server, failing over to another region) takes hours to reach everyone.
- **Short TTLs** (30 to 60 seconds): fast failover and **DNS-based load balancing** (return different addresses to different clients), at the cost of more lookups.

Next, a short check on what you just read.
