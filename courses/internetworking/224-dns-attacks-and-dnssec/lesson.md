# DNS Attacks and DNSSEC

*Chapter 7 · DNS.*

DNS was designed in the 1980s, for a network of researchers who trusted each other. Answers came over UDP, with **no signature and no encryption**. A resolver believed any reply that matched its question. Some popular attacks follow straight from that.

## Some popular DNS hacks

**Cache poisoning.** The attacker floods a caching resolver with forged replies, hoping one arrives before the real answer and matches the query's **16-bit ID**. One win poisons the cache for every user until the TTL expires. In 2008 Dan Kaminsky showed how to make this fast and reliable. The quick fix was to also randomize the **source port**, so an attacker has to guess about 32 bits instead of 16.

**Amplification DDoS.** The attacker sends small queries with a **spoofed source address**, the victim's, to many **open resolvers** (resolvers that answer anyone). A 60-byte question asking for every record (`ANY`) can bring back a reply of several kilobytes, all of it aimed at the victim. That's why servers now refuse `ANY` and resolvers shouldn't answer strangers.

**DNS tunneling.** Remember tunneling from chapter 1: a firewall that allows DNS may let anything hidden *inside* DNS through. Malware encodes stolen data in names it looks up, like `c2VjcmV0.attacker.com`, and the attacker's server reads it from the queries. Signs: lots of long, random-looking names going to one domain.

**Hijacking and typosquatting.** Take over the domain's **registrar account**, change its NS records, and you own the whole domain. Or register `rnarshall.edu` and wait for typos.

## DNSSEC

**DNSSEC (DNS Security Extensions)** adds **digital signatures** to records, so a resolver can check that an answer really came from the zone's owner and wasn't changed.

| Record | Job |
|---|---|
| **RRSIG** | The signature over a set of records |
| **DNSKEY** | The zone's public key, to check the signatures |
| **DS** | A hash of the child zone's key, published in the **parent** zone |
| **NSEC / NSEC3** | Signed proof that a name **doesn't** exist |

The DS records form a **chain of trust**: the root signs `edu`'s key, `edu` signs `marshall.edu`'s, and so on. A resolver only has to trust the **root's key**.

What DNSSEC **doesn't** do: **encrypt**. Anyone on the path still sees which names you look up. For privacy there's **DNS over TLS** (DoT, port 853) and **DNS over HTTPS** (DoH, port 443), which encrypt the link between you and your resolver.

Next, a check on attacks and DNSSEC.
