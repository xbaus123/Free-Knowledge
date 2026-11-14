# Clients and Resolvers

*Chapter 7 · DNS.*

The part of DNS on your own machine is called the **resolver**.

## What a client needs

To look anything up, client software needs just **two pieces of information**:

1. The **fully qualified domain name (FQDN)** to look up.
2. The **IP address of a nameserver** to ask.

The second one usually comes from **DHCP** (chapter 4), along with your address and gateway. You can see it in `/etc/resolv.conf` on Linux and macOS (`nameserver 192.168.1.1`), or in `ipconfig /all` on Windows.

It has to be an **address**, not a name. You can't look up your nameserver's name without already having a nameserver.

## Stub resolvers and recursive resolvers

- A **stub resolver** is the small resolver built into your OS. It doesn't walk the tree itself: it sends the whole question to one nameserver and waits for the final answer.
- A **recursive resolver** (also called a caching server) does the real work: it asks the root, then the TLD, then the domain's servers, and caches what it learns. Your home router, your ISP, or a public service like `1.1.1.1` or `8.8.8.8` plays this role.

## What a resolver keeps track of

RFC 1034 describes the state a resolver keeps while it works on one question:

| Field | What it holds |
|---|---|
| **SNAME** | The domain **name** being searched for |
| **STYPE** | The query **type** (A, MX, ...) |
| **SCLASS** | The query **class** (IN) |
| **SLIST** | The **list of nameservers** (and the zone they serve) that the resolver is currently trying, best first |
| **SBELT** | The "**safety belt**": a list of servers from a **config file**, like SLIST but pre-loaded, used when the resolver knows nothing better (the root servers, for instance) |
| **CACHE** | Results from **previous queries**, so the next lookup can skip the trip |

SNAME, STYPE, and SCLASS are the question. SLIST and SBELT say who to ask. CACHE is the memory that makes DNS fast.

Next, a check on clients and resolvers.
