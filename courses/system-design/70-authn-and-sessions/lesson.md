# Authentication, Sessions, and Tokens

*Chapter 2 · The Front Door.*

## Authentication and authorization

Two questions, often confused:

- **Authentication** (*authn*): *who are you?* Proving identity with a password, a key, a certificate, a passkey, or a token issued by someone who already checked.
- **Authorization** (*authz*): *what may you do?* Deciding whether this identity may perform this action on this resource.

Authentication happens once per login. Authorization happens on **every request**, for every resource it touches.

### Storing credentials

If you store passwords, never store them in plain text or with a fast hash like SHA-256, which a GPU can try billions of times a second. Use a **slow, salted** password hash: **Argon2**, **scrypt**, or **bcrypt**. The **salt** (random bytes stored with each hash) makes identical passwords hash differently, which defeats precomputed tables. The **work factor** makes each guess expensive. Better yet, offer **passkeys** (WebAuthn): the private key never leaves the user's device, so there's no shared secret to steal from your database or phish from the user.

## Sessions and tokens

After login, every later request must carry proof of identity. There are two families:

**Server-side sessions.** The server stores a session record (`session id → user, expiry`) and gives the client an **opaque**, random session id, usually in a cookie. Every request looks the id up.

- Revocation is trivial: delete the record.
- But every request needs a lookup in a shared session store (chapter 5), which every service must reach.

**Self-contained tokens.** The server packs the identity into the token itself and **signs** it. Any service holding the verification key can check it locally, with no lookup.

- Verification is fast and needs no shared state, which suits many services and many regions.
- But a token stays valid until it expires, even after the user logs out or is banned. You can't easily take it back.

The usual compromise: short-lived **access tokens** (5 to 15 minutes) that services verify locally, plus a long-lived **refresh token** that the client trades for new access tokens. The authorization server checks the refresh token against its database on each exchange, so revoking it ends access within one access-token lifetime. With **refresh token rotation**, each refresh token is single-use: if a stolen one is ever reused, the server sees the duplicate and revokes the whole chain.

Next, a short check on what you just read.
