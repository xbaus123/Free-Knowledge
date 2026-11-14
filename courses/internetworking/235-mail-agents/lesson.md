# Who Handles a Message

*Chapter 8 · Mail.*

A message passes through several programs on its way. Each has a name ending in **agent**.

## The cast

| Agent | Short for | What it does | Examples |
|---|---|---|---|
| **MUA** | Mail **user** agent | The program you read and write mail in | Outlook, Apple Mail, Thunderbird, Gmail in a browser |
| **MSA** | Mail **submission** agent | Accepts new mail from your MUA, after you log in | Your provider's server on port 587 |
| **MTA** | Mail **transfer** agent | Relays mail server to server, looking up MX records | Sendmail, Postfix, Exim, Exchange |
| **MDA** | Mail **delivery** agent | Drops the message into the recipient's mailbox | Dovecot's delivery agent, procmail, Exchange |

The MSA and MTA are usually the same server program wearing two hats. The names still matter, because they use different ports and different rules (more on that later).

## A message's journey

Alice at `example.org` writes to Bob at `example.com`:

1. Alice's **MUA** connects to her provider's **MSA**, logs in, and submits the message.
2. Her provider's **MTA** asks DNS for the **MX** of `example.com`, then the **A** record of the host it names.
3. It opens a **TCP** connection to Bob's **MTA** on port **25** and hands the message over with **SMTP**.
4. Bob's MTA passes it to the **MDA**, which files it in Bob's **mailbox**.
5. Later, Bob's **MUA** fetches it with **IMAP** or **POP**.

SMTP carries mail **toward** the recipient (steps 1 and 3). IMAP and POP are only for **reading** it (step 5). Sending and reading are different protocols.

## Store and forward

Every server on the path **stores** the message (writes it to disk in a **queue**) before it **forwards** it. That's the same idea as AUTODIN's message switching in chapter 1, and it's what makes mail asynchronous:

- If the next hop is down, the message waits in the queue and the server **retries**, typically for up to about **five days**.
- Only when it gives up does the sender get a **bounce**: a message back saying delivery failed.
- A message can pass through several MTAs: a company's spam filter, then its internal server, for example.

Next, a check on the agents.
