# Talking SMTP

*Chapter 8 · Mail.*

**SMTP**, the Simple Mail Transfer Protocol, is how mail moves toward its recipient. It's a **text** protocol: the client sends short commands, one per line, and the server answers each one with a **three-digit code** and some text. You could type it by hand, and administrators often do when they're testing a server.

## A whole conversation

Here's `mail.example.org` delivering Alice's message to Bob's server. `C:` is the client (the sending MTA), `S:` is the server:

```
S: 220 mx.example.com ESMTP ready
C: EHLO mail.example.org
S: 250-mx.example.com Hello mail.example.org
S: 250-SIZE 35882577
S: 250-STARTTLS
S: 250 8BITMIME
C: MAIL FROM:<alice@example.org>
S: 250 OK
C: RCPT TO:<bob@example.com>
S: 250 OK
C: DATA
S: 354 Start mail input; end with <CRLF>.<CRLF>
C: From: Alice <alice@example.org>
C: To: Bob <bob@example.com>
C: Subject: Lunch?
C:
C: Are you free on Friday?
C: .
S: 250 OK: queued as 4F2A91
C: QUIT
S: 221 Bye
```

## The commands

| Command | What it does |
|---|---|
| **HELO** / **EHLO** | "Hello, I'm this host." **EHLO** (extended hello) asks the server to list the extras it supports, like `STARTTLS` and `SIZE`. HELO is the original, plain version |
| **MAIL FROM:** | Starts a message and gives the **sender's** address, where bounces go |
| **RCPT TO:** | One **recipient**. Repeat it for each one |
| **DATA** | "Here comes the message." The server says 354, and the client sends the headers, a blank line, the body, and finally a line holding **just a dot** |
| **QUIT** | End the session |
| **RSET** | Reset: throw away the message in progress, but keep the connection |
| **VRFY** | Verify: "does this mailbox exist?" Handy for testing, and for spammers harvesting addresses, so most servers refuse to answer it |
| **NOOP** | Do nothing, just get a 250. Keeps a connection alive |

## The lone dot

The message ends at a line containing only `.`. So what if the body itself has a line that starts with a dot? The client adds a **second dot** in front of it (**dot-stuffing**), and the receiver takes one away. That way a dot on its own line can only mean "end of message".

## STARTTLS

Plain SMTP is readable by anyone on the path. If the server's EHLO reply lists **STARTTLS**, the client can send `STARTTLS`, and the rest of the conversation runs inside an encrypted TLS session, starting again from EHLO. It's opportunistic: if either side doesn't support it, the mail usually goes in the clear.

Next, a check on the SMTP conversation.
