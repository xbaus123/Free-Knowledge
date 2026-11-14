# What DNS Does

*Chapter 7 · DNS.*

Every routing decision in chapter 6 started from an IP address. People don't type IP addresses, though: they type `marshall.edu`. The **Domain Name System (DNS)** is what turns the name into the address.

## The Internet's contact list

Think of DNS as the contact list on your phone. You tap a name; the phone looks up the number. DNS does two lookups:

- **Forward**: name to address. `www.example.com` → `93.184.215.14`.
- **Reverse**: address to name. `93.184.215.14` → a name, if the owner set one up.

Before DNS, every host on ARPANET downloaded one file, `HOSTS.TXT`, from a single computer at SRI. By the early 1980s the file changed faster than people could copy it. DNS (RFCs 1034 and 1035, 1987) replaced it with a **distributed database**: no single machine holds every name. Your computer still has a small leftover of the old way, `/etc/hosts`, checked before DNS.

## Application, but also infrastructure

DNS sits at the **application layer**: it's a program talking to other programs. But almost every other application depends on it, so it behaves like **infrastructure**. When DNS breaks, the network is "up" but nothing seems to work: the web, mail, and logins all fail at the first step.

## How it talks

- **Client-server.** Your machine (the client) asks; a **nameserver** answers.
- **UDP, port 53.** A lookup is one small question and one small answer, so DNS skips TCP's handshake. If the answer is lost, the client just asks again.
- **TCP, port 53**, for the big jobs: copying a whole zone between servers, or an answer too large for one UDP packet.

## How programs call it

A program rarely builds DNS packets itself. It calls a library function and the OS does the rest:

| Call | Asks for | Gets back |
|---|---|---|
| `gethostbyname("www.example.com")` | A forward lookup | The address (**A** record), following any alias (**CNAME**) on the way |
| `gethostbyaddr("93.184.215.14")` | A reverse lookup | A name, from a record under **in-addr.arpa** |

(Modern code uses `getaddrinfo` and `getnameinfo`, which also handle IPv6, but the idea is the same.)

Next, a quick check on what DNS does and how it talks.
