# SMTP Reply Codes

*Chapter 8 · Mail.*

Every server line starts with a three-digit code. The **first digit** tells the client almost everything it needs to know.

## The first digit

| First digit | Meaning | What the client does |
|---|---|---|
| **2**xx | **Success** | Carry on |
| **3**xx | **Keep going**: the server needs more | Send the rest (after `DATA`, that's the message) |
| **4**xx | **Temporary failure** | Keep the message and **try again later** |
| **5**xx | **Permanent failure** | Stop, and **bounce** the message to the sender |

The difference between **4** and **5** is the one that matters most. A 4xx says "not now", so the message stays in the queue. A 5xx says "never", so retrying is pointless.

## Codes you'll see

| Code | Meaning |
|---|---|
| **220** | Service ready (the greeting) |
| **221** | Closing the connection (after QUIT) |
| **250** | OK, done |
| **354** | Start mail input (after DATA) |
| **421** | Service not available, closing (the server is overloaded or shutting down) |
| **450** / **451** | Mailbox busy, or a local error: try later |
| **452** | Not enough storage right now |
| **500** / **501** | Syntax error in the command or its arguments |
| **502** | Command not implemented (often the answer to VRFY) |
| **503** | Bad sequence of commands (DATA before RCPT TO, say) |
| **550** | Mailbox unavailable: no such user, or refused by policy |
| **552** | Exceeded storage allocation (the mailbox or message is too big) |
| **554** | Transaction failed (often: rejected as spam) |

## Multi-line replies

A reply can take several lines. Every line but the **last** has a **dash** after the code, and the last has a **space**: `250-SIZE`, `250-STARTTLS`, `250 8BITMIME`. That's how the client knows the reply is finished.

## Greylisting

Some servers answer an unknown sender's first attempt with a deliberate **451**, "try again later". A real MTA queues the message and comes back in a few minutes, and is let in. A lot of spam software never retries, so it's simply dropped. It works only because 4xx means **retry**.

Next, a check on reply codes.
