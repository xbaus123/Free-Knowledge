# JWT Pitfalls

*Chapter 2 · The Front Door.*

## Pitfalls

JWT libraries have a long history of vulnerabilities, almost all from trusting the token to describe how it should be checked:

- **`alg: none`.** The standard allows unsigned tokens. Some libraries accepted a token with `"alg": "none"` and an empty signature as valid. Anyone could write their own claims.
- **Algorithm confusion.** A server expecting RS256 is handed a token with `"alg": "HS256"`. A naive library uses the "key" it has (the RSA *public* key, which is public!) as the HMAC secret, and the attacker's self-signed token verifies. The fix for both: the **verifier decides** which algorithms it accepts; the token's header only selects among them.
- **Skipping claim checks.** A valid signature only proves the issuer made the token. Without checking `aud`, a token issued for a low-security internal tool works against your payments API.
- **Timing attacks.** Comparing signatures with `==` stops at the first differing byte, so response time leaks how many leading bytes were right. With enough measurements, an attacker can forge a signature byte by byte. Use a **constant-time** comparison.
- **Clock skew.** Servers' clocks disagree by seconds (chapter 7), so allow a small **leeway** (30 to 60 seconds) when checking `exp` and `nbf`.
- **Where the browser keeps it.** A token in `localStorage` can be stolen by any injected script (**XSS**). A token in an `HttpOnly` cookie can't be read by scripts, but the browser sends it automatically, which opens up **cross-site request forgery (CSRF)**; defend with `SameSite` cookies and anti-CSRF tokens.

Next, a short check on what you just read.
