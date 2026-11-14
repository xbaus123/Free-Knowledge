# What DNS Gives Away

*Chapter 7 · DNS.*

DNS is public on purpose: anyone has to be able to find your web and mail servers. That makes it the first stop for an attacker sizing up a target. Here's what a few queries can reveal.

## Information that can be gathered

| Query | What it tells an attacker |
|---|---|
| **SOA** and **NS** | Who hosts the DNS (Azure, Cloudflare, their own servers), and the admin's mailbox |
| **MX** | Who runs the mail. `marshall-edu.mail.protection.outlook.com` says Microsoft 365, so a phishing email would imitate a Microsoft login page |
| **TXT** | SPF lists every service allowed to send mail as you. Verification tokens reveal which cloud services you use |
| **A** records for guessed names | `vpn.`, `remote.`, `dev.`, `test.`, `admin.`: brute-forcing common names finds forgotten servers |
| **PTR** for a whole address block | Reverse lookups often reveal host names, and so what each machine is |
| **AXFR** (zone transfer) | **Everything.** Every name and address in the zone, in one request |

## Zone transfers

AXFR exists so secondaries can copy a zone. If a server lets **anyone** request it, an attacker gets a complete map of the network in one command:

```
dig axfr example.com @ns1.example.com
```

The fix is simple: **allow zone transfers only to your own secondaries**, by address and ideally with a shared key (TSIG). Most servers now refuse by default, but misconfigured ones still turn up.

## Other leaks

- **HINFO** records announce the OS. Don't publish them.
- **Split DNS** done wrong: internal names like `payroll-db.corp.example.com` leaking into the public zone.
- **Certificate logs**: every HTTPS certificate is logged publicly, names included, so hidden subdomains often aren't.

This kind of gathering is called **reconnaissance**, or **footprinting**. It's legal to look up public records, and defenders should do it to themselves first, to see what they're giving away.

Next, a check on what DNS reveals.
