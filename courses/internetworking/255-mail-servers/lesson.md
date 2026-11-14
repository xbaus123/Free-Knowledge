# Mail Server Software

*Chapter 8 · Mail.*

The MTA is the heart of a mail system. A few programs run most of the world's mail.

## The main ones

| Server | Where it comes from | Notes |
|---|---|---|
| **Sendmail** | Berkeley Unix, 1983 | The original. Hugely flexible, and famous for its cryptic configuration file |
| **Postfix** | IBM Research, 1998 | Built as a safer, simpler replacement for Sendmail. The default on many Linux systems |
| **Exim** | University of Cambridge, 1995 | The default on Debian, and common on web hosting servers |
| **Microsoft Exchange** | Microsoft, 1996 | Mail plus **calendars, contacts, and groupware**, tied to Active Directory. Now mostly sold as **Exchange Online** in Microsoft 365 |

Postfix and Exim only move mail. To store mailboxes and serve **IMAP** and **POP** they're paired with a separate server, usually **Dovecot**. Exchange does both in one product.

## Sendmail's configuration

Sendmail reads **`sendmail.cf`**, a file so dense that almost nobody writes it by hand. Instead, you edit a short macro file, **`sendmail.mc`**, and generate the `.cf` from it with the `m4` macro processor. Two settings show the kind of **re-directing** Sendmail is good at:

- **Egress** (outgoing): a **smart host**. `define(`SMART_HOST', `relay.example.com')` sends all outgoing mail to one relay instead of delivering it directly, so only that relay needs port 25 to the Internet.
- **Ingress** (incoming): the **mailertable**, which maps domains to where their mail should go next: "mail for `corp.example.com` goes to the Exchange server at 10.0.5.20". Sendmail accepts the mail, then **hands it off** to another IP for final delivery.

## Sendmail in front of Exchange

That's the "Sendmail to Exchange" setup in this chapter's slides:

```
Internet ──25──▶ Sendmail relay (in the DMZ) ──▶ Exchange (inside) ◀──587/HTTPS── staff
```

The relay faces the Internet, scans and filters, and forwards clean mail to Exchange. The Exchange server never has to accept a connection from the Internet on port 25. Today the relay is often a cloud filtering service instead: Marshall's MX points at **Exchange Online Protection**, which does exactly this job.

## Run it yourself, or not?

Running your own mail server means keeping it patched, keeping its IP off spam **blocklists**, setting up SPF, DKIM, and DMARC, and handling backups. That's why most organizations now use **hosted** mail (Microsoft 365, Google Workspace) and keep only the DNS records in-house.

Next, a check on mail servers.
