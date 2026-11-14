# MX, PTR, and Other Records

*Chapter 7 · DNS.*

Four more record types, and a museum of old ones.

## MX: where mail goes

An **MX (mail exchange)** record says which host accepts mail for a domain. Each one has a **priority**, and **lower is preferred**:

```
example.com.   IN  MX  10  mail1.example.com.
example.com.   IN  MX  20  mail2.example.com.
```

A sending server tries `mail1` (10) first, and falls back to `mail2` (20) only if mail1 doesn't answer. Two records with the **same** priority share the load. The MX names a *host*, so the sender then needs that host's **A** record.

## PTR: reverse lookups

For address to name, DNS reuses the tree. IPv4 addresses live under **`in-addr.arpa`**, written **backwards**, because DNS names get more specific to the *left* while addresses get more specific to the *right*:

```
192.0.2.10   →   10.2.0.192.in-addr.arpa.   IN  PTR  mail1.example.com.
```

That way `2.0.192.in-addr.arpa` can be delegated to whoever owns the 192.0.2.0/24 block. IPv6 does the same under `ip6.arpa`, one hex digit per label. Mail servers often check that a sender's address has a PTR record; many reject mail from addresses that don't.

## TXT and HINFO

- **TXT**: free text. Today it carries machine-readable policy: **SPF** ("these servers may send mail for my domain") and verification tokens that prove you own a domain.
- **HINFO**: host information, the **CPU and OS** of a host. It's in the original spec, but almost nobody publishes it now. Telling the world your OS version helps attackers pick an exploit.

## The museum

RFC 1035 also defined types that didn't last:

| Type | What it was | What happened |
|---|---|---|
| MD, MF | Mail destination, mail forwarder | Replaced by **MX** |
| MB, MG, MR | Mailbox, mail group, mail rename | Experimental, never caught on |
| MINFO | Mailbox or mail list info | Rarely used |
| NULL | An empty record | Experimental |
| WKS | Well-known services a host offers | Obsolete |

Next, a check on MX, PTR, and friends.
