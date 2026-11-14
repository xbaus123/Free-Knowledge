# Mail Ports

*Chapter 8 · Mail.*

Mail uses a handful of well-known TCP ports. Each one is a different job, and firewalls are configured around them.

## Sending: SMTP

| Port | Name | Used for |
|---|---|---|
| **25** | SMTP | **Server to server** (MTA to MTA). Every public mail server listens here |
| **587** | Submission | **Clients sending** new mail to their own server, after logging in. Usually upgraded with STARTTLS |
| **465** | SMTPS / submissions | Submission over **TLS from the first byte** (implicit TLS). Deprecated for years, then standardized again (RFC 8314), so you'll see both 465 and 587 |

Why split 25 and 587? Port 25 has to accept mail from **anyone** for its own domains, without a password, or nobody could email you. Port 587 accepts mail for **anywhere**, but only from **logged-in users**. Mixing the two jobs on one port is how servers end up as open relays.

Many ISPs **block outbound port 25** from home connections. Infected home computers used to send spam straight to port 25 on servers all over the world. Blocking it forces home users through their provider's port 587, where they have to log in.

## Reading: POP and IMAP

| Port | Protocol | Security |
|---|---|---|
| **110** | POP3 | Plain text (or upgraded with STARTTLS) |
| **995** | POP3S | TLS from the start |
| **143** | IMAP | Plain text (or upgraded with STARTTLS) |
| **993** | IMAPS | TLS from the start |

The pattern: the TLS versions are on **different, higher** ports (995, 993), and the plain versions are the originals (110, 143). Today, use **993** or **995** and close 110 and 143 to the outside.

## Typical setups

The slides for this chapter list three:

- **Sendmail standalone**: one Unix server doing everything, with SMTP on **25** (or **587** for users), **IMAP** on **993**, and **POP** on **995** (or **110**).
- **Sendmail in front of Exchange**: a Sendmail relay faces the Internet and hands mail to an internal **Exchange** server, with users submitting on **587**.
- **Hosted (cloud)**: Microsoft 365 or Google Workspace runs all the ports for you. Marshall's MX points at Microsoft.

Next, a check on mail ports.
