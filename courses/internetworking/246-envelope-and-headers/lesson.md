# The Envelope and the Letter

*Chapter 8 · Mail.*

A paper letter has an **envelope**, which the post office reads, and the **letter** inside, which only the recipient reads. Email has the same split, and the two don't have to agree.

## The envelope

The **envelope** is the SMTP conversation itself: the `MAIL FROM:` and `RCPT TO:` commands. Servers use it to route the message and to know where bounces go. Nobody sees it in their mail program.

## The headers

Everything after `DATA` is the **message**: **headers**, a blank line, then the **body**. The format is set by **RFC 5322**. Headers are `Name: value` lines:

```
From: Alice <alice@example.org>
To: Bob <bob@example.com>
Cc: Carol <carol@example.net>
Subject: Lunch?
Date: Fri, 13 Nov 2026 09:14:02 -0500
Message-ID: <4F2A91@mail.example.org>
```

Your mail program **shows** you the headers. It doesn't show you the envelope.

## Why they're separate

- **Bcc** works because of the split. A Bcc recipient gets a `RCPT TO:` in the envelope but never appears in the headers, so the other recipients can't see them.
- **Mailing lists** keep the original `From:` header, but change the envelope sender to the list's own address, so bounces go to the list software instead of to the person who posted.
- **Spoofing** works because of the split too. Plain SMTP doesn't check that the `From:` header matches anything. A message can say it's from your bank in the header while the envelope says something else entirely. The security lessons later in this chapter are about closing that gap.

## Received: headers, the postmarks

Every MTA that handles a message adds a **`Received:`** header **at the top**:

```
Received: from mail.example.org (mail.example.org [198.51.100.20])
        by mx.example.com with ESMTPS id 4F2A91
        for <bob@example.com>; Fri, 13 Nov 2026 09:14:03 -0500
Received: from [10.0.0.15] (alice-laptop)
        by mail.example.org with ESMTPSA
        for <bob@example.com>; Fri, 13 Nov 2026 09:14:02 -0500
```

To follow a message's path, read the `Received:` headers from the **bottom up**: the bottom one is the first hop (Alice's laptop to her server), and the top one is the last (into Bob's server). This is how administrators trace delayed or forged mail. The receiving server also records the envelope sender in a **`Return-Path:`** header.

Next, a check on envelopes and headers.
