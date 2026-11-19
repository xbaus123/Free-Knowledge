# Security and Identity: TLS, OAuth, JWTs, and Access Control

*Chapter 2 · The Front Door.*

Implement what the security readings described: JWT verification that resists the classic attacks, role-based access control, and a gateway that combines them.

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
- Find the routes with this method whose prefix matches whole path segments (as in the load balancer lab), and use the **longest**. No match is `(404, None)`.
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
