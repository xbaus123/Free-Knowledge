import json
import unittest
from unittest import mock

import solution
from solution import Gateway, InvalidToken, Policy, b64url_decode, b64url_encode, sign, verify

NOW = 1_700_000_000
KEYS = {"2026-10": b"current-secret", "2026-07": b"previous-secret"}
ISS = "https://auth.example.com"
AUD = "orders-api"


def claims(**overrides):
    c = {"iss": ISS, "aud": AUD, "sub": "user-42", "exp": NOW + 300, "iat": NOW, "roles": ["customer"]}
    c.update(overrides)
    return {k: v for k, v in c.items() if v is not None}


def token(kid="2026-10", key=None, alg="HS256", **overrides):
    return sign({"alg": alg, "typ": "JWT", "kid": kid}, claims(**overrides), key or KEYS[kid])


def check(t, now=NOW):
    return verify(t, KEYS, ISS, AUD, now)


def tamper(t, **changes):
    """Rewrites a token's claims but keeps its original signature."""
    head, body, sig = t.split(".")
    c = json.loads(b64url_decode(body))
    c.update(changes)
    return f"{head}.{b64url_encode(json.dumps(c).encode())}.{sig}"


class VerifyTest(unittest.TestCase):
    def test_valid(self):
        """returns the claims of a valid token"""
        c = check(token())
        self.assertEqual(c["sub"], "user-42")
        self.assertEqual(c["roles"], ["customer"])

    def test_malformed(self):
        """rejects tokens that aren't three base64url JSON parts"""
        for bad in ["", "abc", "a.b", "a.b.c.d", "!!!.???.***", b64url_encode(b"[1]") + ".e30.", "e30.bm90IGpzb24.e30"]:
            with self.assertRaises(InvalidToken, msg=repr(bad)):
                check(bad)

    def test_tampered_claims(self):
        """rejects a token whose claims were changed after signing"""
        with self.assertRaises(InvalidToken):
            check(tamper(token(), roles=["admin"]))
        with self.assertRaises(InvalidToken):
            check(tamper(token(), sub="user-1"))

    def test_wrong_key(self):
        """rejects a token signed with a key the gateway doesn't trust"""
        with self.assertRaises(InvalidToken):
            check(token(key=b"attacker-secret"))

    def test_alg_none(self):
        """rejects alg none, even with an empty signature"""
        head = b64url_encode(json.dumps({"alg": "none", "kid": "2026-10"}).encode())
        body = b64url_encode(json.dumps(claims(roles=["admin"])).encode())
        with self.assertRaises(InvalidToken):
            check(f"{head}.{body}.")
        for alg in ["None", "NONE", "HS512", "RS256"]:
            with self.assertRaises(InvalidToken, msg=alg):
                check(token(alg=alg))

    def test_key_rotation(self):
        """picks the key by kid, so old tokens work until their key is retired"""
        self.assertEqual(check(token(kid="2026-07"))["sub"], "user-42")
        with self.assertRaises(InvalidToken):
            verify(token(kid="2026-07"), {"2026-10": KEYS["2026-10"]}, ISS, AUD, NOW)
        with self.assertRaises(InvalidToken, msg="kid that doesn't match the key"):
            check(token(kid="2026-07", key=KEYS["2026-10"]))
        with self.assertRaises(InvalidToken, msg="no kid"):
            check(sign({"alg": "HS256"}, claims(), KEYS["2026-10"]))

    def test_constant_time(self):
        """compares signatures with hmac.compare_digest"""
        with mock.patch.object(solution.hmac, "compare_digest", wraps=solution.hmac.compare_digest) as cmp:
            check(token())
            self.assertTrue(cmp.called, "a == comparison leaks, through timing, how many bytes matched")

    def test_issuer(self):
        """rejects tokens from another issuer"""
        with self.assertRaises(InvalidToken):
            check(token(iss="https://evil.example.com"))
        with self.assertRaises(InvalidToken):
            check(token(iss=None))

    def test_audience(self):
        """rejects tokens meant for another service"""
        with self.assertRaises(InvalidToken):
            check(token(aud="billing-api"))
        with self.assertRaises(InvalidToken):
            check(token(aud=None))
        self.assertEqual(check(token(aud=["billing-api", AUD]))["sub"], "user-42", "aud may be a list")
        with self.assertRaises(InvalidToken):
            check(token(aud=["billing-api"]))

    def test_expiry(self):
        """rejects expired tokens, allowing 30 seconds of clock skew"""
        t = token(exp=NOW)
        self.assertEqual(check(t, now=NOW + 29)["sub"], "user-42")
        with self.assertRaises(InvalidToken):
            check(t, now=NOW + 30)
        with self.assertRaises(InvalidToken, msg="a token without exp never expires: refuse it"):
            check(token(exp=None))

    def test_not_before(self):
        """rejects tokens before their nbf time, with the same leeway"""
        t = token(nbf=NOW + 100)
        with self.assertRaises(InvalidToken):
            check(t, now=NOW + 69)
        self.assertEqual(check(t, now=NOW + 70)["sub"], "user-42")


ROLES = {
    "customer": {"permissions": ["orders:read", "orders:create"]},
    "support": {"permissions": ["orders:refund", "users:read"], "inherits": ["customer"]},
    "manager": {"permissions": ["reports:*"], "inherits": ["support"]},
    "admin": {"permissions": ["*"]},
    "loop-a": {"permissions": ["a:read"], "inherits": ["loop-b"]},
    "loop-b": {"permissions": ["b:read"], "inherits": ["loop-a"]},
}


class PolicyTest(unittest.TestCase):
    def test_direct(self):
        """grants a role's own permissions"""
        p = Policy(ROLES)
        self.assertEqual(p.permissions(["customer"]), {"orders:read", "orders:create"})
        self.assertTrue(p.allows(["customer"], "orders:read"))
        self.assertFalse(p.allows(["customer"], "orders:refund"))

    def test_inheritance(self):
        """grants inherited permissions, transitively"""
        p = Policy(ROLES)
        self.assertEqual(
            p.permissions(["manager"]),
            {"reports:*", "orders:refund", "users:read", "orders:read", "orders:create"},
        )
        self.assertTrue(p.allows(["manager"], "orders:create"))
        self.assertTrue(p.allows(["customer", "support"], "users:read"))

    def test_cycles(self):
        """survives roles that inherit from each other"""
        self.assertEqual(Policy(ROLES).permissions(["loop-a"]), {"a:read", "b:read"})

    def test_wildcards(self):
        """'resource:*' grants every action on it, and '*' grants everything"""
        p = Policy(ROLES)
        self.assertTrue(p.allows(["manager"], "reports:export"))
        self.assertFalse(p.allows(["manager"], "reportsx:export"))
        self.assertFalse(p.allows(["manager"], "users:delete"))
        self.assertTrue(p.allows(["admin"], "users:delete"))

    def test_fails_closed(self):
        """grants nothing for unknown roles or no roles"""
        p = Policy(ROLES)
        self.assertEqual(p.permissions(["root", "superuser"]), set())
        self.assertFalse(p.allows([], "orders:read"))
        self.assertFalse(p.allows(["root"], "orders:read"))


ROUTES = [
    ("GET", "/orders", "orders:read"),
    ("POST", "/orders", "orders:create"),
    ("POST", "/orders/refunds", "orders:refund"),
    ("GET", "/me", None),
]


def gateway():
    return Gateway(ROUTES, Policy(ROLES), KEYS, ISS, AUD)


def bearer(t):
    return {"Authorization": f"Bearer {t}"}


class GatewayTest(unittest.TestCase):
    def test_forwards_identity(self):
        """forwards authorized requests with the verified identity"""
        status, up = gateway().handle("GET", "/orders/7", bearer(token(roles=["support", "customer"])), NOW)
        self.assertEqual(status, 200)
        self.assertEqual(up["x-user-id"], "user-42")
        self.assertEqual(up["x-user-roles"], "customer,support")

    def test_unauthenticated(self):
        """returns 401 without a valid bearer token"""
        g = gateway()
        self.assertEqual(g.handle("GET", "/orders", {}, NOW), (401, None))
        self.assertEqual(g.handle("GET", "/orders", {"Authorization": token()}, NOW), (401, None))
        self.assertEqual(g.handle("GET", "/orders", {"Authorization": "Basic dXNlcjpwYXNz"}, NOW), (401, None))
        self.assertEqual(g.handle("GET", "/orders", bearer(token(exp=NOW - 60)), NOW), (401, None))
        self.assertEqual(g.handle("GET", "/orders", bearer(tamper(token(), roles=["admin"])), NOW), (401, None))

    def test_header_case(self):
        """treats header names case-insensitively"""
        status, _ = gateway().handle("GET", "/orders", {"authorization": f"Bearer {token()}"}, NOW)
        self.assertEqual(status, 200)

    def test_forbidden(self):
        """returns 403 when the caller lacks the route's permission"""
        g = gateway()
        self.assertEqual(g.handle("POST", "/orders/refunds", bearer(token()), NOW), (403, None))
        self.assertEqual(g.handle("POST", "/orders/refunds", bearer(token(roles=["support"])), NOW)[0], 200)
        self.assertEqual(g.handle("GET", "/orders", bearer(token(roles=None)), NOW), (403, None))

    def test_routing(self):
        """matches method and the longest whole-segment prefix"""
        g = gateway()
        self.assertEqual(g.handle("POST", "/orders", bearer(token()), NOW)[0], 200)
        self.assertEqual(g.handle("POST", "/orders/refunds/9", bearer(token()), NOW)[0], 403)
        self.assertEqual(g.handle("DELETE", "/orders/7", bearer(token()), NOW), (404, None))
        self.assertEqual(g.handle("GET", "/ordersx", bearer(token()), NOW), (404, None))
        self.assertEqual(g.handle("GET", "/me", bearer(token(roles=[])), NOW)[0], 200, "None: any authenticated caller")

    def test_strips_spoofed_identity(self):
        """drops identity headers the client sent itself"""
        headers = {**bearer(token()), "X-User-Id": "user-1", "X-User-Roles": "admin", "X-User-Email": "a@b.c", "Accept": "application/json"}
        status, up = gateway().handle("GET", "/orders", headers, NOW)
        self.assertEqual(status, 200)
        self.assertEqual(up["x-user-id"], "user-42")
        self.assertEqual(up["x-user-roles"], "customer")
        self.assertNotIn("x-user-email", up)
        self.assertEqual(up["accept"], "application/json", "other headers pass through")


if __name__ == "__main__":
    unittest.main()
