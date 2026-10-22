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
    raise NotImplementedError


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
        return set()

    def allows(self, user_roles, permission):
        return False


# --- 3. An authenticating gateway --------------------------------------------


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
        raise NotImplementedError
