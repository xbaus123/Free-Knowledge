# The DNS Hierarchy

*Chapter 7 · DNS.*

DNS names are a **tree**, read right to left. Each piece between the dots is a **label**.

```
. (root)
├── com                 ← top-level domain (TLD)
│   └── example         ← second-level domain
│       └── www         ← a host
├── edu
│   └── marshall
│       └── mail
└── org
```

`www.example.com.` means: start at the **root** (the final dot), go to `com`, then `example`, then `www`.

## The levels

| Level | Examples | Run by |
|---|---|---|
| **Root** | `.` | 13 named root server identities, `a.root-servers.net` to `m.root-servers.net` (hundreds of physical copies) |
| **Top-level domain (TLD)** | Generic: `com`, `org`, `edu`, `gov`. Country code: `uk`, `de`, `jp` | A registry for each TLD |
| **Second-level** | `example.com`, `marshall.edu` | Whoever registered the name |
| **Below that** | `www.example.com`, `cs.marshall.edu` | The domain owner, freely |

## Fully qualified names

A **fully qualified domain name (FQDN)** spells out the whole path to the root: `mail.marshall.edu.`. The trailing dot *is* the root. Most tools let you leave it off, but in zone files it matters: without it, the server tacks the zone name on the end.

## Domains, zones, and delegation

Nobody could run the whole tree, so it's split into **zones**. A zone is the part of the tree that one organization's servers answer for. The `com` registry doesn't store `www.example.com`; it stores a **delegation** that says "for anything under `example.com`, ask these nameservers". That's an **NS** record, and it's how one tree is run by millions of separate owners.

## An older tree

The original DNS RFC drew its example tree with the domains of the time:

```
. (root)
├── MIL
│   ├── BRL
│   ├── NOSC
│   └── DARPA
├── EDU
│   ├── UCI
│   ├── MIT
│   │   ├── LCS
│   │   │   └── XX
│   │   └── ACHILLES
│   ├── ISI
│   │   └── A, C, VAXA, VENERA, Mockapetris
│   ├── UDEL
│   └── YALE
└── ARPA
    ├── IN-ADDR
    ├── SRI-NIC
    └── ACC
```

So the host `XX` has the full name `XX.LCS.MIT.EDU.`, read from the leaf up to the root.

`MIL` for the military, `EDU` for universities, and `ARPA`, which still holds `in-addr.arpa` for reverse lookups today. (Paul Mockapetris designed DNS; he named a host after himself in the example.)

Next, a check on the tree.
