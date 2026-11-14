# Project: Plan Your Mail

*Chapter 8 · Mail.*

Chapter 7 gave your project network its names. Now decide how it handles mail.

## The questions

**1. How will you use mail?**
- **Internally**: staff writing to each other, shared mailboxes (`support@`, `info@`), calendars, and alerts from servers and printers.
- **Externally**: staff writing to the world, **customers** writing to you, and automated mail you send them (receipts, password resets, newsletters).

**2. What will you use for your server?**

| Option | Good for | You run |
|---|---|---|
| **Hosted** (Microsoft 365, Google Workspace) | Almost every small and mid-sized organization | Just the DNS records and the user accounts |
| **Your own** (Postfix + Dovecot, or Exchange Server) | Strict rules about where data lives, or very large sites | Everything: patching, spam filtering, backups, blocklist monitoring |
| **Hybrid** (a relay in front of internal Exchange, or a filtering service in front of hosted mail) | Gradual migrations, extra filtering | The relay, plus the internal server |

Bulk mail to customers (newsletters, receipts) usually goes through a separate **sending service**, so a spam complaint about a newsletter can't get your staff mail blocklisted. Add it to SPF and give it its own DKIM key.

**3. What clients will you use?**
Pick from webmail, mobile apps, desktop clients, and groupware. That decides which ports you need: **443** for webmail, ActiveSync, and Outlook on Exchange; **587** and **993** for desktop IMAP clients. Don't offer **POP** or the plain ports (**110**, **143**) unless something really needs them.

**4. How will you keep public and private mail separated?**
- **Internal-only addresses** (like `alerts@corp.example.com` for printers and servers) are accepted only from inside the network. The internal relay doesn't take mail from the Internet at all.
- **Public mail** comes in through **one** door: the MX, pointing at a filtering service or a relay in the DMZ, never directly at an internal server.
- Use the **split DNS** from chapter 7: the public zone has only the MX, SPF, DKIM, and DMARC records. Internal mail server names stay in the internal zone.
- Outbound **DLP** rules stop internal-only information from going out.

## A worked example

The chapter 5 office, using `example.com` and Microsoft 365:

| Record | Type | Value | Zone |
|---|---|---|---|
| `example.com` | MX 0 | `example-com.mail.protection.outlook.com` | Public |
| `example.com` | TXT | `v=spf1 include:spf.protection.outlook.com include:mail.newsletter.example -all` | Public |
| `selector1._domainkey.example.com` | CNAME | Microsoft's DKIM key for the domain | Public |
| `_dmarc.example.com` | TXT | `v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com` | Public |
| `relay.corp.example.com` | A | 192.168.10.231 (Postfix, internal only) | Internal |

Staff use Outlook (443) and the Outlook app. Printers and servers send alerts to `relay.corp.example.com`, which only accepts connections from 192.168.10.0/24 and forwards to Microsoft 365 as a smart host. Port 25 is closed inbound at the firewall, because nothing inside needs to receive mail from the Internet. The DMARC policy starts at `p=none`, and moves to `quarantine` after two weeks of clean reports.

(A CNAME *can* be used for a DKIM key: it's an ordinary TXT lookup, and that's how Microsoft 365 lets you publish its keys. The no-CNAME rule is for the **target of an MX**.)

## Questions your write-up should answer

- Who uses mail, internally and externally, and for what?
- Hosted, self-run, or hybrid, and why?
- Which clients will users run, and which ports does that mean opening?
- What are your MX, SPF, DKIM, and DMARC records?
- How are internal-only mail and public mail kept apart?
- How do you stop the server becoming an open relay, and how are attachments scanned?

Next, a check on planning mail.
