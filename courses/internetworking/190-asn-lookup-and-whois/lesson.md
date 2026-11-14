# Tools: IP to ASN and whois

*Chapter 6 · Routing.*

traceroute shows the routers. These tools tell you **whose** they are.

## IP to ASN

Every public address belongs to a prefix that some AS announces in BGP. Lookup sites (search "IP to ASN") take an address and tell you the AS, its name, and the announced prefix:

| Address | ASN | Who |
|---|---|---|
| 8.8.8.8 | AS15169 | Google |
| 1.1.1.1 | AS13335 | Cloudflare |

Run it on each hop of a traceroute and you can see the packet cross from your ISP's AS into a transit provider and then into the destination's AS: the inter-domain path, made visible.

## whois

The `whois` command looks up records in the databases kept by the registries. Ask about an **IP address** and you get the **RIR**'s record for it:

```
$ whois 8.8.8.8
NetRange:   8.8.8.0 - 8.8.8.255
CIDR:       8.8.8.0/24
OriginAS:   AS15169
Organization: Google LLC
...
OrgAbuseEmail: ...
```

That tells you the block it belongs to, which AS originates it, the organization, which RIR holds the record (here, ARIN), and an **abuse contact**.

Ask about a **domain** and you get the domain's registration:

```
$ whois example.com
Registrar:         ...
Creation Date:     ...
Registry Expiry Date: ...
Name Server:       A.IANA-SERVERS.NET
```

The registrar, when it was created and when it expires, and its name servers (DNS, coming later in the course). Personal details of the owner are often **redacted** for privacy.

## Why security people use these

- **Investigating an attack**: an unknown address keeps hitting your server. whois tells you whose it is and where to send an abuse report.
- **Spotting phishing**: a "bank" domain created last week is a red flag.
- **Checking routing**: an address that suddenly maps to an unexpected AS may be a BGP hijack.
- **Reconnaissance**: attackers use the same tools to map a target's networks, so assume your own records are public.

Next, a check on these tools.
