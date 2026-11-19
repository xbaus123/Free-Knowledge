# TLS and the Handshake

*Chapter 2 · The Front Door.*

## TLS: trust on the wire

The network between a client and your servers is hostile: Wi-Fi routers, ISPs, and anyone on the path can read and modify packets. **TLS** (Transport Layer Security; its predecessor was SSL) gives a connection three properties:

- **Confidentiality**: the bytes are encrypted.
- **Integrity**: any modification is detected.
- **Server authentication**: the client knows it's talking to the real `api.example.com`, not an impostor.

## The handshake

Chapter 1 counted TLS 1.3's handshake as one extra round trip. Here's what happens in it:

1. The client sends supported cipher suites and a **key share**: half of an ephemeral Diffie-Hellman (ECDHE) exchange.
2. The server replies with its own key share. Both sides now derive the same **session keys** without ever sending them. Everything after this point is encrypted.
3. The server sends its **certificate** and a signature over the handshake made with the certificate's private key, proving it holds that key.
4. The client validates the **certificate chain**: the server's certificate is signed by an intermediate, which is signed by a **root certificate authority (CA)** the client already trusts. It checks that the certificate hasn't expired and that it names the host the client wanted.

Because the session keys come from **ephemeral** keys thrown away after the handshake, a stolen server private key can't decrypt recorded past traffic. That's **forward secrecy**, and TLS 1.3 requires it. The expensive part is the asymmetric cryptography in steps 1 to 3. Afterward, bulk encryption with AES-GCM or ChaCha20 is cheap, and **session resumption** lets a returning client skip most of the handshake. TLS 1.3's **0-RTT** mode even sends data with the first packet, but an attacker can replay that data, so servers accept it only for idempotent requests (chapter 1).

Next, a short check on what you just read.
