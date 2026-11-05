# What Makes the Internet Special

*Chapter 1 · Intro to Networks.*

Plenty of networks existed before the Internet. Four design ideas, and an open way of agreeing on standards, are what let it outgrow all of them.

## What makes the Internet special

Douglas Comer's *Internetworking with TCP/IP* lists four ideas that set the Internet apart from the networks before it:

1. **Network technology independence.** TCP/IP doesn't care whether the wire underneath is Ethernet, Wi-Fi, fiber, or a satellite link. Any network that can carry a packet can join.
2. **Universal interconnection.** Every host gets an address, and any host can reach any other one, no matter which networks lie between them.
3. **End-to-end acknowledgments.** The two endpoints confirm delivery with each other directly, not hop by hop. The network in the middle can stay simple.
4. **Application protocol standards.** Standard protocols for common jobs (email, file transfer, the web, remote login) mean programs from different vendors work together.

## Who sets the rules: the IETF and RFCs

Nobody owns the Internet, but someone has to write down how it works. That's the **Internet Engineering Task Force (IETF)**, an open community of engineers: anyone can join a working group's mailing list, and decisions are made by "rough consensus and running code."

- **RFCs** (*Requests for Comments*) are the Internet's numbered technical documents. The name dates back to RFC 1 in 1969, when they really were requests for feedback. An RFC is never edited after it's published: a later RFC replaces it.
- **Standards** start as working drafts (*Internet-Drafts*). Once a working group agrees, a draft is published as an RFC on the **standards track**. Famous examples include RFC 791 (IP), RFC 9293 (TCP), and RFC 1035 (DNS).
- You can read every RFC for free at [www.ietf.org](https://www.ietf.org) and [rfc-editor.org](https://www.rfc-editor.org).

Next, a short check on the four ideas and how Internet standards are made.
