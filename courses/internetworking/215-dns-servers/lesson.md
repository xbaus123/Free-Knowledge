# Kinds of DNS Servers

*Chapter 7 · DNS.*

Not all nameservers do the same job. There are three roles, and one machine can play more than one.

## Authoritative servers

An **authoritative server** holds the real data for a zone. It:

- **Responds to queries** about names in its zone, with the **AA** flag set.
- **Performs zone updates**: changes from the administrator, or from DHCP when a laptop registers its new address (dynamic DNS).
- **Performs zone exchanges**: sends copies of the zone to its secondaries.

## Secondary servers

A zone needs at least two nameservers, preferably on different networks, so one failure can't take the domain offline. The **primary** holds the master copy; **secondary** servers hold copies.

- The secondary checks the primary's **SOA serial** every **refresh** interval, and pulls a fresh copy when the serial goes up.
- It copies the zone with a **zone transfer** (**AXFR**) over **TCP**.
- If the primary is down, the secondary keeps answering, until the SOA's **expire** time runs out.

Clients don't know or care which is which: secondaries are just as authoritative as the primary.

## Caching servers

A **caching server** (the recursive resolver from earlier) holds no zones of its own. It looks things up for its clients and **saves previously returned values**, so repeat lookups come back in a millisecond instead of several round trips.

Its answers are **non-authoritative**: nslookup says so right at the top (`Non-authoritative answer:`), and dig's flags lack `aa`.

## Why attackers target caching servers

A caching server is trusted by **every client behind it**, and it keeps what it learns until the TTL runs out. So if an attacker can slip **one forged answer** into its cache, say `bank.com → attacker's address`, then **every user** of that server is sent to the attacker, for as long as the TTL lasts. Nobody's computer was hacked; they all just asked the wrong server at the wrong time. This is **cache poisoning**, and it's in the security lesson.

Next, a check on server roles.
