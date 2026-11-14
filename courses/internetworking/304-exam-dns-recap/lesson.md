# Exam 3 Review: DNS, Mail, and the Upper Layers

*Chapter 9 · Upper Layers.*

The second half of the review: **DNS** (the hierarchy, the components, and **quite a bit on `dig` and `nslookup`**), **mail**, and this chapter's **session** and **application (HTTP)** layers.

## DNS in one screen

- **The hierarchy**: the **root** (`.`), then **TLDs** (`com`, `edu`, `uk`), then **domains** (`marshall.edu`), then hosts (`www.marshall.edu`). Each level **delegates** to the one below with NS records.
- **The components**: the **client** (a **stub resolver** in your OS), a **recursive resolver** (your ISP's, your router, or 1.1.1.1) that does the legwork and caches, and **authoritative servers** that hold the zone's records.
- **Records**: **A** / **AAAA** (name to address), **CNAME** (alias), **MX** (mail, with priority), **NS** (the zone's servers), **SOA** (the zone's settings), **PTR** (address to name), **TXT** (SPF, DMARC).

## dig and nslookup

| You want | nslookup | dig |
|---|---|---|
| An address | `nslookup marshall.edu` | `dig marshall.edu` |
| The MX records | `set type=mx`, then the name | `dig mx marshall.edu` |
| A reverse lookup | `nslookup 52.101.42.14` | `dig -x 52.101.42.14` |
| Ask a specific server | `nslookup marshall.edu 1.1.1.1` | `dig @1.1.1.1 marshall.edu` |
| Just the answer | | `dig +short marshall.edu` |
| Walk the tree from the root | | `dig +trace marshall.edu` |

Reading `dig` output: **status** (`NOERROR`, `NXDOMAIN`, `SERVFAIL`), **flags** (`qr` response, `rd` recursion desired, `ra` recursion available, **`aa` authoritative**), the **ANSWER** section, and the **TTL** (seconds left in the cache).

## Mail and the upper layers

- Mail: the sender looks up the **MX**, MTAs talk **SMTP** on **25**, clients submit on **587**, and read with **IMAP** (**993**) or **POP** (**995**).
- Session layer: establish, dialogue control (**simplex**, **half duplex**, **full duplex**), synchronization, checkpointing, terminate. **SIP**: register, INVITE, BYE.
- Application layer: **HTTP** on **80**, **HTTPS** on **443**, the nine methods, and status code classes.

Next, the last drill before the project.
