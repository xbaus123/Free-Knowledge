# Email Security

*Chapter 8 · Mail.*

Email is the most common way into an organization. The protocols were designed for a small, trusting network, and the three issues from the start of the chapter, **hacking**, **attachments**, and **privacy**, all come from that.

## Hacking

- **Phishing**: a message that imitates someone you trust, usually to steal a password or get you to open an attachment. **Spear phishing** targets one person using details about them. **Business email compromise** pretends to be the boss asking for an urgent wire transfer.
- **Spoofing**: SMTP doesn't check the `From:` header, so anyone can claim to be anyone. Fixing this is what SPF, DKIM, and DMARC (next lesson) are for.
- **Open relays**: a server that will forward mail **from anyone to anywhere**. Spammers find them within hours, and the server's IP lands on every blocklist. A mail server should relay only for its own domains (incoming) and its own logged-in users (outgoing).
- **Address harvesting**: `VRFY` and `EXPN` reveal valid mailboxes, so they're switched off.
- **Banner disclosure**: a 220 greeting like `Sendmail 8.12.3` tells an attacker which exploits to try. Keep it plain.
- **Account takeover**: a stolen password lets an attacker read mail and send phishing from a trusted account. **MFA** (chapter 2) is the fix.

## Attachments

Covered in the MIME and filtering lessons: scan, block risky types, sandbox, and teach users that a file name proves nothing.

## Privacy

Plain SMTP, POP, and IMAP send **everything in the clear**, including passwords.

- **TLS** fixes this **hop by hop**: STARTTLS between servers, and ports 587, 993, and 995 for clients. But each server along the way still **decrypts** the message, stores it, and can read it.
- STARTTLS between servers is **opportunistic**: an attacker in the path can strip the `STARTTLS` line out of the EHLO reply, and the servers fall back to plain text (a **downgrade attack**). **MTA-STS** and **DANE** let a domain publish "always use TLS with me".
- **End-to-end encryption**, with **S/MIME** (certificates) or **PGP** (keys you manage), encrypts the message itself, so only the recipient can read it. Few people use it, because both ends have to set it up.

## Rules for a mail server

1. **No open relay.** Test it from outside.
2. Require **TLS and a login** for submission (587/465), and TLS for reading (993/995).
3. Disable **VRFY** and **EXPN**, and trim the banner.
4. **Scan** everything, both ways.
5. Publish **SPF, DKIM, and DMARC**, and a **PTR** for the server's address.
6. **MFA** on every mailbox, and phishing training for every user.

Next, a check on email security.
