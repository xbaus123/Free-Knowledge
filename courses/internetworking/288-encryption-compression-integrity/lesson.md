# Encryption, Compression, and Integrity

*Chapter 9 · Upper Layers.*

The other three presentation jobs, one at a time.

## Encryption

Encryption turns readable **plaintext** into unreadable **ciphertext** with a **key**. Only someone with the right key can decrypt it.

| Kind | Keys | Speed | Used for |
|---|---|---|---|
| **Symmetric** (AES) | **One** shared secret key | Fast | Encrypting the bulk of the data |
| **Asymmetric** (RSA, elliptic curve) | A **public** key and a **private** key | Slow | Agreeing on a symmetric key, and signatures |

**TLS**, which protects HTTPS, IMAPS, and SIP over TLS, uses **both**: asymmetric cryptography at the start to agree on a key, then fast symmetric encryption for everything after.

## Compression

| Kind | Can you get the original back exactly? | Examples | Good for |
|---|---|---|---|
| **Lossless** | **Yes** | gzip, Brotli, ZIP, PNG | Text, code, web pages, files |
| **Lossy** | **No**, some detail is thrown away | JPEG, MP3, H.264 video | Photos, audio, video |

Text compresses very well: a web page often shrinks to a fifth of its size with gzip. A browser says what it can handle with `Accept-Encoding: gzip, br`, and the server answers `Content-Encoding: gzip`.

## Integrity checks

A **hash** like **SHA-256** turns any data into a short fixed-size fingerprint. Change one bit of the data and the fingerprint changes completely.

- A **checksum** or **CRC** (chapters 3 and 4) catches **accidental** damage, like noise on a wire.
- A plain hash doesn't stop an **attacker**, who can change the data and recompute the hash. A **MAC** (message authentication code) mixes in a secret key, so only someone with the key can make a valid one.

Next, a check on these three jobs.
