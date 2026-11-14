# The Presentation Layer

*Chapter 9 · Upper Layers.*

The session layer manages the conversation. The **presentation layer** makes sure both sides **understand what's being said**. It's sometimes called the **translator** of the network.

## Its four jobs

| Job | Question it answers | Examples |
|---|---|---|
| **Data translation** | Do we agree on the format? | ASCII, UTF-8, JSON, byte order |
| **Encryption and decryption** | Can anyone else read it? | TLS, AES |
| **Compression** | Can we send fewer bytes? | gzip, JPEG, MP3 |
| **Integrity checks** | Did it arrive unchanged? | SHA-256 hashes, MACs |

## Why translation matters

Two machines can store the **same** information in **different** ways:

- Old IBM mainframes store text in **EBCDIC**, where the letter `A` is byte 193. Most other computers use **ASCII**, where `A` is byte 65.
- Some processors store a number's most significant byte first (**big-endian**), others last (**little-endian**).

If nobody translates, the receiver reads nonsense. So the presentation layer converts data from the sender's format into a **common format** for the trip, and from that into whatever the receiver uses. Converting from anything into a shared format like ASCII is what gives systems **interoperability**: they can work together without knowing how each other works inside.

## The order matters

When you send, the jobs happen in a sensible order: **compress first, then encrypt**. Encrypted data looks random, and random data doesn't compress. On the way in, the receiver undoes them in reverse: decrypt, then decompress.

Next, a check on the presentation layer's jobs.
