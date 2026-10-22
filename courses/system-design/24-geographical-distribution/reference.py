"""Running in many regions: global traffic routing with data residency,
a counter that merges across active-active regions, and CDN caching rules."""

import math
from urllib.parse import parse_qsl, urlencode, urlsplit


def distance_km(a, b):
    """Great-circle distance between two (latitude, longitude) points."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


# --- 1. Global traffic routing -----------------------------------------------


class NoRegion(Exception):
    """No healthy region may serve this user."""


class GlobalRouter:
    """regions: {name: {"location": (lat, lon), "jurisdiction": "EU", "capacity": 1000}}.

    residency: {jurisdiction: set of jurisdictions its users' data may be
    processed in}. Users from a jurisdiction that isn't listed may be served
    anywhere.
    """

    def __init__(self, regions, residency):
        self.regions = regions
        self.residency = residency
        self.down = set()
        self.load = {name: 0 for name in regions}

    def mark_down(self, region):
        self.down.add(region)

    def mark_up(self, region):
        self.down.discard(region)

    def candidates(self, location, jurisdiction):
        """The healthy regions allowed to serve this user, nearest first."""
        allowed = self.residency.get(jurisdiction)
        names = [
            name
            for name, r in self.regions.items()
            if name not in self.down and (allowed is None or r["jurisdiction"] in allowed)
        ]
        return sorted(names, key=lambda n: (distance_km(location, self.regions[n]["location"]), n))

    def route(self, location, jurisdiction):
        """Pick the region for a new request and count it as active there."""
        options = self.candidates(location, jurisdiction)
        if not options:
            raise NoRegion(jurisdiction)
        spare = [n for n in options if self.load[n] < self.regions[n]["capacity"]]
        region = spare[0] if spare else options[0]
        self.load[region] += 1
        return region

    def finish(self, region):
        """A request to region completed."""
        self.load[region] -= 1


# --- 2. Active-active counters -----------------------------------------------


class PNCounter:
    """A counter every region can change locally and merge in any order."""

    def __init__(self, region):
        self.region = region
        self.incs = {}  # region -> total increments made there
        self.decs = {}  # region -> total decrements made there

    def increment(self, n=1):
        self.incs[self.region] = self.incs.get(self.region, 0) + n

    def decrement(self, n=1):
        self.decs[self.region] = self.decs.get(self.region, 0) + n

    def value(self):
        return sum(self.incs.values()) - sum(self.decs.values())

    def merge(self, other):
        """Fold in another replica's state."""
        for mine, theirs in ((self.incs, other.incs), (self.decs, other.decs)):
            for region, count in theirs.items():
                mine[region] = max(mine.get(region, 0), count)


# --- 3. CDN caching rules ----------------------------------------------------

CACHEABLE_STATUS = {200, 301, 404, 410}
IGNORED_PARAMS = ("utm_", "fbclid", "gclid")


def lower_keys(headers):
    return {k.lower(): v for k, v in headers.items()}


def cache_control(value):
    """'public, max-age=60' -> {"public": None, "max-age": "60"}"""
    directives = {}
    for part in value.split(","):
        name, _, arg = part.strip().partition("=")
        if name:
            directives[name.lower()] = arg.strip('"') if arg else None
    return directives


def edge_ttl(request_headers, status, response_headers):
    """How many seconds a shared cache may keep this response (0: don't)."""
    req, resp = lower_keys(request_headers), lower_keys(response_headers)
    cc = cache_control(resp.get("cache-control", ""))
    if status not in CACHEABLE_STATUS or "set-cookie" in resp:
        return 0
    if {"no-store", "private", "no-cache"} & cc.keys():
        return 0
    if "authorization" in req and not ({"public", "s-maxage"} & cc.keys()):
        return 0
    for name in ("s-maxage", "max-age"):
        if name in cc:
            try:
                return max(0, int(cc[name]))
            except (TypeError, ValueError):
                return 0
    return 0


def cache_key(url, request_headers, vary=()):
    """The key a CDN stores a response under, or None if it can't be cached."""
    if any(v.strip() == "*" for v in vary):
        return None
    parts = urlsplit(url)
    params = sorted(
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith(IGNORED_PARAMS)
    )
    key = parts.netloc.lower() + (parts.path or "/")
    if params:
        key += "?" + urlencode(params)
    req = lower_keys(request_headers)
    for name in sorted({v.strip().lower() for v in vary}):
        value = req.get(name, "")
        if name == "accept-encoding":
            value = normalize_encoding(value)
        key += f"|{name}={value}"
    return key


def normalize_encoding(accept_encoding):
    """Collapse the many Accept-Encoding spellings to the one encoding the
    edge will serve: br, gzip, or identity."""
    offered = {e.split(";")[0].strip().lower() for e in accept_encoding.split(",")}
    for encoding in ("br", "gzip"):
        if encoding in offered:
            return encoding
    return "identity"
