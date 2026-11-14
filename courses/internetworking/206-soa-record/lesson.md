# The SOA Record

*Chapter 7 · DNS.*

Every zone has exactly **one** **SOA (start of authority)** record, at the top of the zone. It says who runs the zone and how other servers should keep their copies fresh.

Here's the real SOA for `marshall.edu`, from `dig`:

```
marshall.edu.  3215  IN  SOA  ns1-34.azure-dns.com. dnsadmin.marshall.edu. 2793 3600 1200 259200 3600
```

## The fields

| Field | marshall.edu | Meaning |
|---|---|---|
| **MNAME** | `ns1-34.azure-dns.com.` | The **primary** nameserver for the zone |
| **RNAME** | `dnsadmin.marshall.edu.` | The **mailbox** of the person responsible. The first dot stands for `@`: `dnsadmin@marshall.edu` |
| **Serial** | 2793 | An unsigned 32-bit **version number** of the zone. Bump it on every change |
| **Refresh** | 3600 | Seconds a secondary waits before checking for a new version |
| **Retry** | 1200 | If a refresh fails, seconds to wait before trying again |
| **Expire** | 259200 (3 days) | If a secondary can't reach the primary for this long, it stops answering for the zone: its copy is **no longer authoritative** |
| **Minimum** | 3600 | The minimum TTL for records from this zone. Today it's used as how long to cache a "no such name" answer |

All of the timers are 32-bit values in **seconds**.

## How the timers work together

A secondary server checks the primary's SOA every **refresh** seconds. If the **serial** is higher than its own copy, it pulls the new zone. If the primary is down, it tries again every **retry** seconds, and keeps answering from its old copy until **expire** runs out.

That's why the serial matters: **forget to bump it and the secondaries never pick up your change.** A common habit is a date-based serial, like `2026111301` for the first change on November 13, 2026.

## Another example

`nslookup` shows the same fields with friendlier labels. For `whitehouse.gov`:

```
origin = ernest.ns.cloudflare.com
mail addr = dns.cloudflare.com
serial = 2351553162
refresh = 10000
retry = 2400
expire = 604800
minimum = 1800
```

`origin` is MNAME, `mail addr` is RNAME, and the nameservers belong to Cloudflare: the SOA alone tells you who hosts the zone.

Next, a check on the SOA.
