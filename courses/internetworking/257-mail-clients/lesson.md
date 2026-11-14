# Mail Clients

*Chapter 8 · Mail.*

The mail user agent is the part people actually see. There are five broad kinds.

| Kind | Examples | How it reaches the mail |
|---|---|---|
| **Cloud (web-based)** | Gmail, Outlook on the web | A website over **HTTPS**. Nothing to install |
| **Mobile apps** | Gmail app, Outlook app, iOS Mail | IMAP, ActiveSync, or the provider's own API, with **push** notifications |
| **Command line** | mutt, Alpine, pine, elm, `mail` | IMAP or POP, or reading the mailbox file straight off a Unix server |
| **Desktop** | Outlook, Apple Mail, Mozilla Thunderbird | IMAP, POP, or Exchange's protocols. Keeps a local copy for offline use |
| **Groupware** | Exchange, HCL (formerly IBM) Notes, Salesforce | Mail joined to calendars, contacts, tasks, or a customer database |

## Command-line clients

They look old, and they are: **elm** (1986) and **pine** (1989) were how university students read mail before the web. **Alpine** is pine's successor, and **mutt** ("all mail clients suck, this one just sucks less") is still popular with administrators. They matter because:

- They work over **SSH** on a server with no screen at all.
- `mail` can be used from **scripts**: `echo "Backup failed" | mail -s "Alert" admin@example.com`. Cron jobs and monitoring tools send alerts this way.

## Groupware

Groupware treats mail as one part of working together. Exchange invites you to a meeting, and accepting it updates your **calendar**. Salesforce logs every email to a customer against that customer's **record**. For a business, that integration is often the real reason to choose a mail system.

## What it means for the network

Each kind of client needs different doors open:

- Webmail and most mobile apps: just **HTTPS (443)**.
- Desktop clients on IMAP: **587** to send and **993** to read.
- Exchange's Outlook and ActiveSync: **443**.

Knowing which clients your users run tells you which ports and services you need, and which you can keep closed.

Next, a check on mail clients.
