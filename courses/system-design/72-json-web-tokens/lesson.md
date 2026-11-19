# JSON Web Tokens

*Chapter 2 · The Front Door.*

## JSON Web Tokens

A **JWT** (pronounced "jot") is the standard self-contained token. It's three base64url-encoded parts joined by dots:

```text
eyJhbGciOiJIUzI1NiIsImtpZCI6IjIwMjYtMTAifQ.eyJpc3MiOiJodHRwczovL2F1dGguZXhh...
\________________ header ________________/ \_______________ payload ________...
```

```json
{"alg": "HS256", "typ": "JWT", "kid": "2026-10"}
{"iss": "https://auth.example.com", "sub": "user-42", "aud": "orders-api",
 "exp": 1700000300, "iat": 1700000000, "roles": ["customer"]}
```

The third part is the **signature** over `header.payload`. The registered **claims** in the payload:

| Claim | Meaning | Why check it |
|---|---|---|
| `iss` | Issuer: who created the token | A token from someone else's auth server proves nothing |
| `sub` | Subject: who the token is about | The identity you'll act on |
| `aud` | Audience: which service the token is for | Stops a token meant for one service being replayed against another |
| `exp` | Expiry time (Unix seconds) | Bounds how long a stolen token is useful |
| `nbf`, `iat` | Not-before and issued-at times | Rejects tokens used too early |
| `jti` | A unique token id | Lets you keep a denylist, or detect replays |

A JWT is **signed, not encrypted**. Anyone can base64-decode the payload and read it, so never put secrets in it.

## Signing algorithms

- **HS256** (HMAC with SHA-256) uses one **shared secret** both to sign and to verify. It's fast, but every verifier can also *mint* tokens, so the secret must stay among parties that fully trust each other.
- **RS256** (RSA) and **ES256** (elliptic curve) are **asymmetric**: the authorization server signs with a private key, and services verify with the public key. A compromised service can't forge tokens. Authorization servers publish their public keys as a **JWKS** (JSON Web Key Set) at a well-known URL.

Every token names its key in the header's `kid` (key id). That's what makes **key rotation** painless: publish the new key, start signing with it, and keep the old key trusted until every token signed with it has expired. Then retire it.

Next, a short check on what you just read.
