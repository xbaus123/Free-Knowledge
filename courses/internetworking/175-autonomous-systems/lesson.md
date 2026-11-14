# Autonomous System Numbers

*Chapter 6 · Routing.*

To take part in inter-domain routing, a network needs an **autonomous system number (ASN)**. An AS is a group of IP prefixes run by one operator, usually an ISP or a large organization, with a single routing policy.

## Number ranges

ASNs started as **16-bit** numbers and ran short, much like IPv4 addresses. **32-bit** ASNs were added in 2007.

| Range | Size | Use |
|---|---|---|
| 1 – 64,495 | 16-bit | Public ASNs |
| 64,496 – 64,511 | 16-bit | Documentation and examples (like this course) |
| **64,512 – 65,534** | 16-bit | **Private**, for use inside an organization |
| 65,536 – 4,199,999,999 | 32-bit | Public ASNs |
| 4,200,000,000 – 4,294,967,294 | 32-bit | Private |

0 and 65,535 (and 4,294,967,295) are reserved. Private ASNs work like private IP addresses: fine internally, never announced to the Internet.

## Three types of AS

```
 stub:          [ AS ]──── provider

 multi-homed:   provider 1 ────[ AS ]──── provider 2      (doesn't carry others' traffic)

 transit:       AS ────[ ISP ]──── AS                      (carries traffic between other ASes)
                          │
                          AS
```

| Type | Connections | Carries other ASes' traffic? |
|---|---|---|
| **Stub** | One provider | No: only its own traffic in and out |
| **Multi-homed** | Two or more providers, for redundancy | No |
| **Transit** | Many | **Yes**: that's its business (ISPs) |

A stub AS barely needs BGP: a default route to its one provider would do. Multi-homing is the usual reason a company gets its own ASN.

## Where ASNs come from

Same chain as IP addresses: **IANA** (the Internet Assigned Numbers Authority) hands blocks to the five **Regional Internet Registries (RIRs)**, which handle requests:

| RIR | Region |
|---|---|
| **ARIN** | North America |
| **RIPE NCC** | Europe, the Middle East, and Central Asia |
| **APNIC** | Asia-Pacific |
| **LACNIC** | Latin America and the Caribbean |
| **AFRINIC** | Africa |

Next, a check on ASNs.
