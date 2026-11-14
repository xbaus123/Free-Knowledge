# Where Mail Fits

*Chapter 8 · Mail.*

Chapter 7 gave every host a name. This chapter puts those names to work on one of the oldest and busiest applications on the Internet: **email**.

## Up the stack

Mail lives at the top of the OSI model, in the **application layer**. Under it sits everything from earlier chapters:

| Layer | What mail uses |
|---|---|
| 7 Application | **SMTP** to send, **IMAP** or **POP** to read, **DNS** to find servers |
| 4 Transport | **TCP**: every mail protocol is a TCP conversation |
| 3 Network | IP addresses, from the servers' **A** and **AAAA** records |
| 2 and 1 | Whatever links sit between the servers: Ethernet, fiber, Wi-Fi |

## A quick recap: DHCP

Before a laptop can send any mail, it needs an address. Chapter 4's **DHCP** hands one out, along with the gateway and the **DNS servers** to use:

- DHCP runs over **UDP**. The **server** listens on port **67** and the **client** on port **68**.
- Four messages: **D**iscover, **O**ffer, **R**equest, **A**ck (**DORA**).
- Microsoft's DHCP server can also register each client's name in DNS (dynamic DNS), so names stay current as addresses change.

## A quick recap: the records mail needs

From chapter 7, the records that matter most for mail:

| Record | Job | Why mail cares |
|---|---|---|
| **SOA** | One per zone: who's in charge, and the timers | Says which servers are authoritative for the domain |
| **NS** | The zone's nameservers | Where a sender's resolver asks the MX question |
| **MX** | Where mail goes, **with priorities** | The heart of mail delivery |
| **A** / AAAA | Name to address, **unique** per name and address | Turns the MX's host name into an IP |
| **CNAME** | An alias | **Never** the target of an MX: an MX must name a real host |
| **PTR** (`in-addr.arpa`) | Address to name | Receivers check that a sending server's address has one |

The rest of the chapter follows a message from your fingers to someone else's inbox: who handles it, how the sender finds the server, what the servers say to each other, and how the whole thing gets attacked and defended.

Next, a quick check to warm up.
