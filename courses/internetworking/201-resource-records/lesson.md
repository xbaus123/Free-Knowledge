# Resource Records

*Chapter 7 · DNS.*

Everything DNS stores is a **resource record (RR)**. Each one has the same five parts:

```
www.example.com.   3600   IN   A   93.184.215.14
└── name ───────┘  └TTL┘ class type └── data ──┘
```

- **Name**: what the record is about.
- **TTL** (time to live): how many seconds other servers may **cache** it. Not the IP header's TTL, which counts hops.
- **Class**: almost always `IN`, for Internet.
- **Type**: what kind of record.
- **Data**: the answer itself.

## The core four

| Type | Name | What it holds |
|---|---|---|
| **A** | Address | An IPv4 address for the name. The name-to-address mapping |
| **AAAA** | "Quad A" | An IPv6 address (four times as long as an A record's) |
| **CNAME** | Canonical name | An **alias**: "this name is really that name" |
| **NS** | Nameserver | Which servers are **authoritative** for a zone |

## CNAME, the alias

```
www.example.com.    IN  CNAME  example.com.
example.com.        IN  A      93.184.215.14
```

Ask for `www.example.com` and the server answers "that's an alias for `example.com`", then you look that up. That's how `gethostbyname` can return an A record even when the name you typed was a CNAME.

Aliases are handy: point `www`, `ftp`, and `shop` at one real host, and you only change one A record when the server moves. The rule to remember: a name that **is** a CNAME can't have other records beside it, because the alias stands for the whole name.

## One name, many addresses

A name can have **several A records**. The server hands them all back, usually in a rotating order:

```
mail.example.com.   IN  A   192.0.2.10
mail.example.com.   IN  A   192.0.2.11
```

That's **DNS round robin**, a cheap way to spread load. More on that in DNS Tricks.

Next, a check on records.
