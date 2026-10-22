"""Verifying JWTs, role-based access control, and an authenticating gateway."""

import base64
import hashlib
import hmac
import json


class InvalidToken(Exception):
    """The token can't be trusted. The message says why."""


def b64url_encode(data):
    """bytes -> base64url text without padding, as JWTs use."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text):
    """base64url text, with or without padding -> bytes. Raises ValueError
    for text that isn't base64url."""
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign(header, claims, key):
    """Issue an HS256 token, as the authorization server would. key is bytes."""
    head = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    body = b64url_encode(json.dumps(claims, separators=(",", ":")).encode())
    mac = hmac.new(key, f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{b64url_encode(mac)}"


# --- 1. Verifying tokens -----------------------------------------------------


def verify(token, keys, issuer, audience, now, leeway=30):
    """Check token and return its claims, or raise InvalidToken.

    keys: {kid: secret bytes}, the signing keys currently trusted.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise InvalidToken("malformed")
    head, body, sig = parts
    try:
        header = json.loads(b64url_decode(head))
        claims = json.loads(b64url_decode(body))
        signature = b64url_decode(sig)
    except ValueError:
        raise InvalidToken("malformed") from None
    if not isinstance(header, dict) or not isinstance(claims, dict):
        raise InvalidToken("malformed")

    # Trust nothing in the token until its signature checks out, and let
    # the verifier, not the token, decide which algorithm that means.
    if header.get("alg") != "HS256":
        raise InvalidToken("unsupported algorithm")
    kid = header.get("kid")
    if not isinstance(kid, str) or kid not in keys:
        raise InvalidToken("unknown key")
    expected = hmac.new(keys[kid], f"{head}.{body}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise InvalidToken("bad signature")

    if claims.get("iss") != issuer:
        raise InvalidToken("wrong issuer")
    aud = claims.get("aud")
    if audience not in (aud if isinstance(aud, list) else [aud]):
        raise InvalidToken("wrong audience")
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)) or now >= exp + leeway:
        raise InvalidToken("expired")
    nbf = claims.get("nbf")
    if nbf is not None and (not isinstance(nbf, (int, float)) or now < nbf - leeway):
        raise InvalidToken("not yet valid")
    return claims


# --- 2. Role-based access control --------------------------------------------


class Policy:
    """roles: {role: {"permissions": [...], "inherits": [...]}}.

    A permission is "resource:action", like "orders:read". "orders:*" grants
    every action on orders, and "*" grants everything.
    """

    def __init__(self, roles):
        self.roles = roles

    def permissions(self, user_roles):
        """Every permission user_roles grant, including inherited ones."""
        granted, seen, todo = set(), set(), list(user_roles)
        while todo:
            role = todo.pop()
            if role in seen or role not in self.roles:
                continue
            seen.add(role)
            granted.update(self.roles[role].get("permissions", []))
            todo.extend(self.roles[role].get("inherits", []))
        return granted

    def allows(self, user_roles, permission):
        resource = permission.split(":", 1)[0]
        granted = self.permissions(user_roles)
        return bool({permission, f"{resource}:*", "*"} & granted)


# --- 3. An authenticating gateway --------------------------------------------


def _matches(prefix, path):
    return path == prefix or path.startswith(prefix.rstrip("/") + "/")


class Gateway:
    """routes: [(method, path prefix, permission)]. A permission of None lets
    any authenticated caller through."""

    def __init__(self, routes, policy, keys, issuer, audience):
        self.routes = list(routes)
        self.policy = policy
        self.keys = keys
        self.issuer = issuer
        self.audience = audience

    def handle(self, method, path, headers, now):
        """Return (status, upstream headers): (200, headers) to forward the
        request, or (401, None), (403, None), or (404, None)."""
        headers = {k.lower(): v for k, v in headers.items()}
        scheme, _, token = headers.get("authorization", "").partition(" ")
        if scheme != "Bearer" or not token:
            return 401, None
        try:
            claims = verify(token, self.keys, self.issuer, self.audience, now)
        except InvalidToken:
            return 401, None

        matching = [r for r in self.routes if r[0] == method and _matches(r[1], path)]
        if not matching:
            return 404, None
        _, _, permission = max(matching, key=lambda r: len(r[1]))
        roles = claims.get("roles", [])
        if permission is not None and not self.policy.allows(roles, permission):
            return 403, None

        upstream = {k: v for k, v in headers.items() if not k.startswith("x-user-")}
        upstream["x-user-id"] = str(claims.get("sub", ""))
        upstream["x-user-roles"] = ",".join(sorted(roles))
        return 200, upstream
