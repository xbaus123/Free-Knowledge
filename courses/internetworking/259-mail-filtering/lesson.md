# What Mail Servers Do Besides Deliver

*Chapter 8 · Mail.*

A modern mail server, or the filtering service in front of it, does a lot more than pass messages along. Every message has to sit on the server for a moment anyway, and that's the chance to inspect it.

## Store and forward, as a feature

Because the server **stores** each message before forwarding it, it can:

- **Queue** mail while the next hop is down, and retry.
- **Hold** suspicious messages in **quarantine** for a person to release or delete.
- **Delay** delivery on purpose, as greylisting does.

## Malware detection

Every attachment is scanned with **antivirus** signatures, and the server checks for warning signs: executables, macros in Office files, password-protected archives (which scanners can't open), and file names like `invoice.pdf.exe`. Many servers simply **block** risky types outright.

## "Dirty word" search

**Content filtering** scans the text of messages against word lists and patterns:

- **Inbound**: profanity, scam phrases, and spam signs.
- **Outbound**: **data loss prevention** (DLP). It flags or blocks messages that contain things like credit card numbers, Social Security numbers, or anything marked "Confidential", so they don't leave by accident (or on purpose).

## Sandboxing

Signatures only catch malware someone has seen before. A **sandbox** opens the attachment in an **isolated virtual machine**, watches what it does (does it download something? edit the registry? encrypt files?), and blocks the message if it misbehaves. Links can be handled the same way: the server **rewrites** every URL so that clicking it goes through a checker first.

## Re-directing

The server can change where mail goes:

- **Aliases** and **forwarding**: `info@` goes to three people, or a departed employee's mail goes to their manager.
- **Routing** by domain: mail for one domain hands off to another server (Sendmail's mailertable).
- **Journaling**: a copy of every message goes to an archive, for legal or compliance reasons.

## Spam scoring

Spam filters (SpamAssassin, for example) add up many small signs: a missing PTR, a failed SPF check, an address on a **blocklist**, spammy words, an odd mix of headers. Above a threshold the message is tagged, quarantined, or rejected.

Next, a check on mail filtering.
