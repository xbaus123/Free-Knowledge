# Tools: nslookup and dig

*Chapter 7 · DNS.*

Two tools let you ask DNS questions by hand. Open a terminal and try them as you read.

| | nslookup | dig |
|---|---|---|
| Age | **Older** | **Newer** (comes with BIND) |
| Platforms | **Every** platform, including Windows | **Most** platforms (Linux, macOS; add-on for Windows) |
| Output | Short and friendly | **More information**: flags, every section, timing |

## nslookup

Run it with a name for a quick lookup, or with no arguments for an interactive prompt where you `set type=`:

```
$ nslookup
> set type=mx
> marshall.edu
Server:   fe80::a416:c0ff:fe30:5464%6
Address:  fe80::a416:c0ff:fe30:5464%6#53

Non-authoritative answer:
marshall.edu    mail exchanger = 0 marshall-edu.mail.protection.outlook.com.
```

`Server` is the resolver it asked: here the home router, on an IPv6 link-local address, port 53. Then `set type=a` and the mail host's name gets you its four addresses.

## dig

```
$ dig mx marshall.edu

;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 52404
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;marshall.edu.                  IN      MX

;; ANSWER SECTION:
marshall.edu.           3076    IN      MX      0 marshall-edu.mail.protection.outlook.com.

;; Query time: 10 msec
;; SERVER: fe80::a416:c0ff:fe30:5464%6#53
```

The sections are the ones from the message format lesson. The parts to read:

- **status**: `NOERROR` (worked), `NXDOMAIN` (no such name), `SERVFAIL` (the server couldn't get an answer).
- **flags**: `qr` = this is a response, `rd` = recursion desired (we asked for it), `ra` = recursion available, `aa` = authoritative answer. **No `aa` here**, so it came from a cache.
- **3076** is the TTL **remaining** in the cache. Ask again and it's lower.
- **Query time**: a cached answer usually takes a few milliseconds.

Useful variations: `dig soa marshall.edu`, `dig -x 52.101.42.14` (reverse lookup), `dig +short marshall.edu` (just the answer), `dig @1.1.1.1 marshall.edu` (ask a specific server), and `dig +trace marshall.edu` (walk the tree from the root, like the resolver algorithm).

## When the answer is empty

```
$ dig mx whitehouse.gov
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 33679
;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 1, ADDITIONAL: 1

;; AUTHORITY SECTION:
whitehouse.gov.   1800   IN   SOA   ernest.ns.cloudflare.com. dns.cloudflare.com. 2351553162 10000 2400 604800 1800
```

`NOERROR` with **ANSWER: 0**: the name exists, but it has **no MX record**. The server sends the zone's **SOA** in the authority section instead, so the resolver knows how long to cache "nothing here" (the SOA's minimum, 1800 seconds). If the name didn't exist at all, the status would be `NXDOMAIN`.

Next, a check on the tools.
