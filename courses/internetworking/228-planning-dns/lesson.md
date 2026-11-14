# Project: Name Your Network

*Chapter 7 · DNS.*

Chapter 5 gave your project network its subnets, and chapter 6 its router. Now give it names.

## The questions

**1. Are you .com, .org, or something else?**

| If you are | A good fit |
|---|---|
| A business | **.com**, or your country's TLD (`.co.uk`, `.de`) if you serve one country |
| A nonprofit or community group | **.org** |
| A school or university | **.edu** (US accredited institutions only) |
| A tech product or service | **.io**, **.dev**, **.app** are popular |

For **internal-only** names, don't make one up like `.local` or `.corp`: use a **subdomain of a domain you own**, such as `corp.example.com`. Then nobody else can ever register it out from under you.

**2. Will you run DNS inside and outside, or DHCP with DNS?**
- **Outside** (the public zone): just the public-facing names, like `www`, `mail`, and the VPN. Usually hosted by your registrar or a DNS provider (Cloudflare, Route 53, Azure DNS), so it survives your office going offline.
- **Inside** (the internal zone): every server, printer, and camera, on private addresses. Run it on your own servers, as a **split** configuration: same domain, different view.
- **DHCP with DNS**: let the DHCP server register each laptop's name as it gets an address (**dynamic DNS**), so `alice-laptop.corp.example.com` always points at the right place.

**3. How will you architect and configure your servers?**
- At least **two** internal nameservers, a **primary** and a **secondary**, in different subnets or racks.
- Zone transfers allowed **only to your secondary**.
- The internal servers do **recursion for internal clients only**. The public authoritative servers do **no** recursion.
- Turn on **DNSSEC** for the public zone if your provider supports it, and validation on your resolvers.
- Hand out the internal resolvers by **DHCP**, and log queries: unusual lookups are an early sign of malware.

**4. Will you use alias (CNAME) records?**
Yes, for **services**, not hosts: `intranet`, `wiki`, and `files` as CNAMEs for the real machines. When a service moves, you change one record, and nobody's bookmarks break.

## A worked example

The chapter 5 office, using `example.com`:

| Name | Type | Value | Zone |
|---|---|---|---|
| `www.example.com` | CNAME | the hosting provider's name | Public |
| `example.com` | MX 10 | `example-com.mail.protection.outlook.com` | Public |
| `example.com` | TXT | SPF: `v=spf1 include:spf.protection.outlook.com -all` | Public |
| `ns1.corp.example.com` | A | 192.168.10.226 | Internal |
| `ns2.corp.example.com` | A | 192.168.10.227 | Internal |
| `files.corp.example.com` | A | 192.168.10.230 | Internal |
| `intranet.corp.example.com` | CNAME | `files.corp.example.com` | Internal |
| Staff laptops | A (dynamic) | Registered by DHCP | Internal |

Both internal nameservers sit in the servers subnet (192.168.10.224/28). The SOA uses a date-based serial, a 1-hour refresh, and a 1-week expire.

## Questions your write-up should answer

- What's your domain name, and why that TLD?
- Which names are public, and which are internal only? Where is each zone hosted?
- How many nameservers do you have, which is primary, and who is allowed zone transfers?
- Does DHCP register names in DNS? Which CNAMEs will you use?
- How are your DNS servers protected (no open recursion, restricted transfers, DNSSEC, logging)?

Next, a check on planning your names.
