# The Top of the Stack

*Chapter 9 · Upper Layers.*

Chapters 7 and 8 lived at the top of the stack: DNS and mail. This chapter finishes the climb. You'll meet the two layers the OSI model squeezes between transport and application, the **session** and **presentation** layers, and then the protocol you use more than any other: **HTTP**.

## The seven layers, one more time

| # | Layer | Job | Examples |
|---|---|---|---|
| 7 | **Application** | What the user's program speaks | HTTP, SMTP, DNS |
| 6 | **Presentation** | How the data is **represented**: format, encryption, compression | ASCII and UTF-8, TLS, gzip |
| 5 | **Session** | Starting, managing, and ending a **conversation** | SIP, RPC, database sessions |
| 4 | Transport | End-to-end delivery | TCP, UDP |
| 3 | Network | Addressing and routing | IP |
| 2 | Data link | One hop | Ethernet, Wi-Fi |
| 1 | Physical | Bits on the medium | Copper, fiber, radio |

Two mnemonics, top down and bottom up:

- **A**ll **P**eople **S**eem **T**o **N**eed **D**ata **P**rocessing (7 to 1)
- **P**lease **D**o **N**ot **T**hrow **S**ausage **P**izza **A**way (1 to 7)

## Where did layers 5 and 6 go?

Recall chapter 1's **TCP/IP model**: it has one **application** layer where OSI has three. On the real Internet, sessions, formats, and encryption are usually handled **inside the application** or by libraries it calls (like a TLS library), not by separate protocols stacked on top of each other.

So why study them? Because the **jobs** are real even when the layers aren't separate. Every video call has to set up a session, every web page has to agree on a character set, and every HTTPS connection encrypts. Knowing which job is which tells you where to look when something breaks.

Next, a quick warm-up.
