# POP and IMAP

*Chapter 8 · Mail.*

SMTP gets mail **to** your mailbox. To **read** it, your mail program uses one of two protocols. Both are text protocols over TCP, like SMTP.

## POP3: download and delete

The **Post Office Protocol** (version 3) works like collecting letters from a PO box:

1. The client logs in (`USER`, `PASS`).
2. It lists the messages (`STAT`, `LIST`) and downloads each one (`RETR`).
3. Usually it deletes them from the server (`DELE`), then `QUIT`s.

After that the mail lives **on the device**. That's simple, it uses little server storage, and it works offline. But read a message on your phone and your laptop never sees it, and if the laptop dies, the mail is gone with it.

## IMAP: keep it on the server

The **Internet Message Access Protocol** keeps mail **on the server**, and clients work on it there:

- **Folders** live on the server, so every device sees the same ones.
- **Flags** (read, flagged, answered) sync across devices.
- Clients can download just the headers, or one part of a message, so a phone doesn't have to fetch a 20 MB attachment to show you the subject.
- The server can **push** new mail to a waiting client (`IDLE`).

The cost: the server stores everything, and it needs backups and quotas.

| | POP3 | IMAP |
|---|---|---|
| Where mail lives | On the device | On the server |
| Several devices | Each sees a different set | All see the same mailbox |
| Folders | Local only | On the server |
| Server storage | Small | Large |
| Ports (plain / TLS) | 110 / 995 | 143 / 993 |

## Other ways in

Not every client uses either. **Webmail** (Gmail, Outlook on the web) is just a website over **HTTPS**: the server does all the IMAP-like work. **Exchange** has its own protocols for Outlook (MAPI over HTTP) and for phones (**ActiveSync**), which also sync calendars and contacts. **JMAP** is a newer, JSON-based alternative to IMAP.

Next, a check on POP and IMAP.
