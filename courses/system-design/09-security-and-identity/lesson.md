# Security and Identity: TLS, OAuth, JWTs, and Access Control

*Part I · Foundations.*

The gateway you built in the last lesson checked a bearer token against a fixed set of API keys. That works for a handful of trusted scripts, but not for a million users, a mobile app, third-party integrations, and dozens of internal services that all need to know **who is calling** and **what they may do**. This lesson is about building that trust across a network: encrypting traffic with TLS, establishing identity with OAuth 2.0 and OpenID Connect, carrying it in signed tokens, and deciding what each identity may do.

Security isn't a feature you bolt on at the end. Like reliability, it's a property of the whole system. A design is only as secure as its weakest trust boundary.

## Start with a threat model

Before choosing tools, decide what you're defending against. **Threat modeling** asks four questions:

1. **What are we building?** Draw the data flows: clients, gateway, services, databases, queues, third parties.
2. **What can go wrong?** Look hardest at the **trust boundaries**, the lines data crosses between parties that trust each other differently: the internet to your edge, your edge to internal services, your services to a vendor's API.
3. **What are we doing about it?**
4. **Did we do a good job?**

Microsoft's **STRIDE** mnemonic is a checklist for question 2. Each threat violates one security property, and each has typical defenses:

| Threat | Violates | Example | Typical defense |
|---|---|---|---|
| **S**poofing | Authenticity | Logging in with a stolen session cookie | Authentication, MFA, short-lived tokens |
| **T**ampering | Integrity | Editing a token's `role` claim to `admin` | Signatures, MACs, TLS |
| **R**epudiation | Non-repudiation | "I never issued that refund" | Tamper-evident audit logs |
| **I**nformation disclosure | Confidentiality | Reading traffic on café Wi-Fi; a leaky error message | Encryption in transit and at rest, least privilege |
| **D**enial of service | Availability | A flood of expensive search requests | Rate limiting (lesson 21), quotas, autoscaling |
| **E**levation of privilege | Authorization | A customer calling an admin-only endpoint | Authorization checks on every request |

Three principles run through every defense:

- **Least privilege**: every user, service, and key gets the minimum access it needs, for the minimum time.
- **Defense in depth**: assume any one layer will fail. Encrypt *and* authenticate *and* authorize *and* audit.
- **Fail closed**: when a check can't be completed (the key is unknown, the policy service is down, the token is malformed), deny. A system that fails open turns every outage into a breach.

## TLS: trust on the wire

The network between a client and your servers is hostile: Wi-Fi routers, ISPs, and anyone on the path can read and modify packets. **TLS** (Transport Layer Security; its predecessor was SSL) gives a connection three properties:

- **Confidentiality**: the bytes are encrypted.
- **Integrity**: any modification is detected.
- **Server authentication**: the client knows it's talking to the real `api.example.com`, not an impostor.

### The handshake

Lesson 2 counted TLS 1.3's handshake as one extra round trip. Here's what happens in it:

1. The client sends supported cipher suites and a **key share**: half of an ephemeral Diffie-Hellman (ECDHE) exchange.
2. The server replies with its own key share. Both sides now derive the same **session keys** without ever sending them. Everything after this point is encrypted.
3. The server sends its **certificate** and a signature over the handshake made with the certificate's private key, proving it holds that key.
4. The client validates the **certificate chain**: the server's certificate is signed by an intermediate, which is signed by a **root certificate authority (CA)** the client already trusts. It checks that the certificate hasn't expired and that it names the host the client wanted.

Because the session keys come from **ephemeral** keys thrown away after the handshake, a stolen server private key can't decrypt recorded past traffic. That's **forward secrecy**, and TLS 1.3 requires it. The expensive part is the asymmetric cryptography in steps 1 to 3. Afterward, bulk encryption with AES-GCM or ChaCha20 is cheap, and **session resumption** lets a returning client skip most of the handshake. TLS 1.3's **0-RTT** mode even sends data with the first packet, but an attacker can replay that data, so servers accept it only for idempotent requests (lesson 4).

### Where to terminate TLS

**Terminating** TLS means decrypting it. Where you do it is an architecture decision:

| Option | How | Gains | Costs |
|---|---|---|---|
| **Terminate at the edge** | The load balancer or gateway decrypts and forwards plain HTTP inside | Certificates in one place; L7 routing, caching, and inspection; servers skip crypto | Traffic inside the network is plaintext: anyone inside can read it |
| **Re-encrypt** (TLS bridging) | The edge decrypts, inspects, and opens a new TLS connection to the backend | L7 features *and* encryption inside | Two handshakes; certificates on every backend |
| **Passthrough** | An L4 balancer forwards encrypted bytes; the backend terminates | True end-to-end encryption; the edge never sees plaintext | No L7 routing, header inspection, or caching at the edge |

Terminating at the edge was the classic setup, on the theory that the internal network is trusted. That theory has failed repeatedly: one compromised machine inside can read everything. The modern stance is **zero trust**: no network location is trusted by default, and every connection is authenticated and encrypted. Inside the data center, that usually means **mutual TLS (mTLS)**, where the *client* also presents a certificate, so both sides know who the other is. Managing certificates for thousands of service instances by hand is impossible, so a service mesh (lesson 30) issues short-lived certificates to every instance automatically, often as **SPIFFE** identities like `spiffe://example.com/orders`.

At the edge, certificates come from a public CA. Automate their issuance and renewal with the **ACME** protocol (as Let's Encrypt does), because an expired certificate is one of the most common self-inflicted outages. One IP address can serve many host names, because the client names the host it wants in the handshake (**SNI**, server name indication), and the server picks the matching certificate.

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
- But every request needs a lookup in a shared session store (lesson 20), which every service must reach.

**Self-contained tokens.** The server packs the identity into the token itself and **signs** it. Any service holding the verification key can check it locally, with no lookup.

- Verification is fast and needs no shared state, which suits many services and many regions.
- But a token stays valid until it expires, even after the user logs out or is banned. You can't easily take it back.

The usual compromise: short-lived **access tokens** (5 to 15 minutes) that services verify locally, plus a long-lived **refresh token** that the client trades for new access tokens. The authorization server checks the refresh token against its database on each exchange, so revoking it ends access within one access-token lifetime. With **refresh token rotation**, each refresh token is single-use: if a stolen one is ever reused, the server sees the duplicate and revokes the whole chain.

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

### Signing algorithms

- **HS256** (HMAC with SHA-256) uses one **shared secret** both to sign and to verify. It's fast, but every verifier can also *mint* tokens, so the secret must stay among parties that fully trust each other.
- **RS256** (RSA) and **ES256** (elliptic curve) are **asymmetric**: the authorization server signs with a private key, and services verify with the public key. A compromised service can't forge tokens. Authorization servers publish their public keys as a **JWKS** (JSON Web Key Set) at a well-known URL.

Every token names its key in the header's `kid` (key id). That's what makes **key rotation** painless: publish the new key, start signing with it, and keep the old key trusted until every token signed with it has expired. Then retire it.

### Pitfalls

JWT libraries have a long history of vulnerabilities, almost all from trusting the token to describe how it should be checked:

- **`alg: none`.** The standard allows unsigned tokens. Some libraries accepted a token with `"alg": "none"` and an empty signature as valid. Anyone could write their own claims.
- **Algorithm confusion.** A server expecting RS256 is handed a token with `"alg": "HS256"`. A naive library uses the "key" it has (the RSA *public* key, which is public!) as the HMAC secret, and the attacker's self-signed token verifies. The fix for both: the **verifier decides** which algorithms it accepts; the token's header only selects among them.
- **Skipping claim checks.** A valid signature only proves the issuer made the token. Without checking `aud`, a token issued for a low-security internal tool works against your payments API.
- **Timing attacks.** Comparing signatures with `==` stops at the first differing byte, so response time leaks how many leading bytes were right. With enough measurements, an attacker can forge a signature byte by byte. Use a **constant-time** comparison.
- **Clock skew.** Servers' clocks disagree by seconds (lesson 26), so allow a small **leeway** (30 to 60 seconds) when checking `exp` and `nbf`.
- **Where the browser keeps it.** A token in `localStorage` can be stolen by any injected script (**XSS**). A token in an `HttpOnly` cookie can't be read by scripts, but the browser sends it automatically, which opens up **cross-site request forgery (CSRF)**; defend with `SameSite` cookies and anti-CSRF tokens.

## OAuth 2.0 and OpenID Connect

Suppose a photo-printing site wants to read your photos from a cloud drive. Giving it your password would hand it your whole account, forever. **OAuth 2.0** is a framework for **delegated authorization**: the user grants a third-party app limited access, and the app never sees the user's password. It defines four roles:

- **Resource owner**: the user.
- **Client**: the app that wants access (the printing site, or your own mobile app).
- **Authorization server**: authenticates the user and issues tokens (Auth0, Okta, Keycloak, Google, or your own).
- **Resource server**: the API holding the data, which accepts the tokens.

### The authorization code flow with PKCE

This is the flow to use for any app with a user:

1. The client generates a random **code verifier** and sends its hash (the **code challenge**) when redirecting the user to the authorization server: `/authorize?client_id=…&scope=photos.read&code_challenge=…&state=…`.
2. The user logs in *at the authorization server*, not at the client, and approves the requested **scopes**.
3. The authorization server redirects back to the client with a short-lived, single-use **authorization code**.
4. The client exchanges the code, plus the original code verifier, for an **access token** (and usually a refresh token) on a direct back-channel request.
5. The client calls the API with `Authorization: Bearer <access token>`.

Why the extra hop through a code? The redirect in step 3 travels through the browser, where URLs leak into history, logs, and `Referer` headers. The code is useless on its own: exchanging it needs the code verifier (**PKCE**, Proof Key for Code Exchange), which never left the client. So an intercepted code can't be redeemed. The `state` parameter ties the response to the request the client made, which stops an attacker from injecting their own code (CSRF on the login flow).

For **service-to-service** calls with no user involved, the **client credentials** flow has a service authenticate directly with its own credentials and receive a token naming the service itself.

### OpenID Connect

OAuth answers "may this app access this API?" It deliberately doesn't say *who the user is*. **OpenID Connect (OIDC)** is a thin identity layer on top. Add the `openid` scope, and the authorization server also returns an **ID token**: a JWT about the authentication itself (`sub`, `email`, when and how the user logged in), intended for the **client**. OIDC also standardizes discovery (`/.well-known/openid-configuration` lists the endpoints and the JWKS URL), so "Sign in with Google" works the same way everywhere.

Keep the two tokens straight: the **ID token** tells the client who logged in, and the **access token** is what the client presents to APIs. An API should never accept an ID token as authorization.

## Authorization models

Once you know *who*, you decide *what*. The models, from simplest to most expressive:

| Model | Rule shape | Good at | Example |
|---|---|---|---|
| **ACL** (access control list) | Each resource lists who may do what | Small numbers of shared objects | File permissions |
| **RBAC** (role-based) | Users have roles; roles grant permissions | Organizations with clear job functions | "support can refund orders" |
| **ABAC** (attribute-based) | Policies over attributes of user, resource, and context | Rules that depend on data | "managers can approve expenses under $5,000 in their own department, during business hours" |
| **ReBAC** (relationship-based) | Permissions follow a graph of relationships | Sharing and nesting | "you can edit a doc if you're an editor of its folder" |

**RBAC** is the common default. Permissions are strings like `orders:refund`. Roles bundle permissions, and roles can **inherit** from other roles, so `manager` gets everything `support` has and more. It's easy to audit (list who has which role), but it struggles when access depends on the specific object: "customers can read *their own* orders" isn't a role. Large systems such as Google's **Zanzibar** (behind Drive and YouTube sharing) and its open-source descendants like SpiceDB use **ReBAC**, storing billions of relationship tuples and answering "can user U do X on object O?" in milliseconds. Policy engines like **Open Policy Agent** let you write ABAC rules as code, separate from the services that enforce them.

### Where to enforce

- **At the gateway**: coarse checks. Is the token valid? Does this caller have `orders:read` at all? Rejecting bad requests at the edge protects every service behind it.
- **In the service**: fine-grained checks. Is order 7 *this user's* order? Only the service has the data to answer. Skipping this check is **broken object-level authorization** (also called IDOR), the most common API vulnerability in the OWASP API Security Top 10: change `/orders/7` to `/orders/8` and read a stranger's order.

The gateway passes the verified identity to services in headers, so it **must strip** any identity headers the client sent itself. Otherwise a client simply sends `X-User-Id: admin`. Services should accept those headers only from the gateway (enforced by mTLS or network policy), or verify the token again themselves.

## Your task

`solution.py` implements token verification, RBAC, and a gateway that combines them. The helpers `b64url_encode`, `b64url_decode`, and `sign` (what the authorization server runs) are done.

### 1. Verifying tokens

`verify(token, keys, issuer, audience, now, leeway=30)` returns the token's claims or raises `InvalidToken`. `keys` maps a key id to its secret bytes. Check, in this order:

1. The token is three base64url parts, and the header and payload are JSON objects. (`b64url_decode` and `json.loads` raise `ValueError` subclasses on bad input.)
2. The header's `alg` is exactly `HS256`. Reject everything else, including `none`.
3. The header's `kid` names a trusted key.
4. The signature is the HMAC-SHA256 of `header.payload` (the original base64url text) with that key. Compare with `hmac.compare_digest`.
5. `iss` equals `issuer`, and `aud` equals `audience` or is a list containing it.
6. `exp` exists and `now < exp + leeway`. If `nbf` exists, `now >= nbf - leeway`.

### 2. Role-based access control

`Policy(roles)` takes `{role: {"permissions": [...], "inherits": [...]}}` (either key may be missing).

- `permissions(user_roles)` returns the set of every permission the roles grant, following `inherits` transitively. Roles may inherit in a cycle, and unknown roles grant nothing.
- `allows(user_roles, permission)` checks a `resource:action` permission. A granted `resource:*` covers every action on that resource, and `*` covers everything.

### 3. The gateway

`Gateway(routes, policy, keys, issuer, audience).handle(method, path, headers, now)` returns `(status, upstream_headers)`:

- Header names are case-insensitive. Lowercase them all.
- `(401, None)` unless `authorization` is `Bearer <token>` and the token verifies.
- Find the routes with this method whose prefix matches whole path segments (as in the last lesson), and use the **longest**. No match is `(404, None)`.
- `(403, None)` if the route's permission isn't allowed for the token's `roles` claim (missing means no roles). A permission of `None` allows any authenticated caller.
- Otherwise `(200, upstream)`: the request's headers, minus every header starting with `x-user-`, plus `x-user-id` (the `sub` claim) and `x-user-roles` (the roles, sorted and joined with commas).

Try the attacks yourself in the **Scratchpad**:

```python
import json
from solution import b64url_decode, sign

t = sign({"alg": "HS256", "kid": "k1"}, {"sub": "me", "roles": ["customer"]}, b"secret")
print(json.loads(b64url_decode(t.split(".")[1])))  # anyone can read the claims
```

## Think about it

- Your gateway uses HS256, so every service that verifies tokens could also mint them. What changes with RS256 and a JWKS endpoint? What new failure appears when the gateway can't fetch the JWKS?
- A user is banned. With 15-minute access tokens and no denylist, how long can they keep using the API? What would a `jti` denylist cost you at 100,000 requests per second?
- Run STRIDE over the capstone's Twitter design. Which trust boundary worries you most?

## Key terms

| Term | Meaning |
|---|---|
| Threat model | A structured list of what can go wrong across a system's trust boundaries |
| STRIDE | Spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege |
| TLS termination | Decrypting TLS at a proxy rather than at the backend |
| Forward secrecy | Past traffic stays secret even if a long-term key leaks later |
| mTLS | TLS where both client and server present certificates |
| Authentication / authorization | Proving who you are / deciding what you may do |
| JWT | A signed, base64url-encoded set of claims |
| `kid` | The key id in a token header, used to pick the verification key and rotate keys |
| OAuth 2.0 | A framework for delegating limited API access without sharing passwords |
| PKCE | Binding an authorization code to a secret the client kept, so intercepted codes are useless |
| OpenID Connect | An identity layer on OAuth that adds the ID token |
| RBAC / ABAC / ReBAC | Access by role / by attributes / by relationships |
| Least privilege | Granting only the access needed, for only as long as needed |
| Fail closed | Denying access whenever a security check can't be completed |
