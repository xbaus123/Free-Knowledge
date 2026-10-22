"""Load balancing algorithms, passive health checks, and an API gateway.

Every balancer shares the Balancer base class: pick() chooses a server
for the next request, and release(server) says a request finished.
"""


class NoHealthyServers(Exception):
    pass


# --- 1. Health ---------------------------------------------------------------


class Balancer:
    """Shared by every algorithm: tracks which servers are healthy."""

    def __init__(self, servers, max_failures=3):
        self.servers = list(servers)
        self.max_failures = max_failures

    def healthy(self):
        """The servers still in rotation, in their original order."""
        return list(self.servers)

    def report(self, server, ok):
        """A request to server succeeded (ok=True) or failed. After
        max_failures failures in a row, take the server out of rotation."""

    def mark_up(self, server):
        """An active health check passed: put server back in rotation."""

    def pick(self):
        candidates = self.healthy()
        if not candidates:
            raise NoHealthyServers()
        return self.choose(candidates)

    def release(self, server):
        """A request to server finished."""

    def choose(self, candidates):
        raise NotImplementedError


# --- 2. Algorithms -----------------------------------------------------------


class RoundRobin(Balancer):
    def __init__(self, servers, max_failures=3):
        super().__init__(servers, max_failures)
        self.next = 0

    def choose(self, candidates):
        server = candidates[self.next % len(candidates)]
        self.next += 1
        return server


class WeightedRoundRobin(Balancer):
    """weights: {server: weight}. Smooth weighted round robin, as in NGINX."""

    def __init__(self, weights, max_failures=3):
        super().__init__(weights, max_failures)
        self.weights = dict(weights)

    def choose(self, candidates):
        raise NotImplementedError


class LeastConnections(Balancer):
    """Sends each request to the server with the fewest active requests.
    self.active[server] counts them."""

    def __init__(self, servers, max_failures=3):
        super().__init__(servers, max_failures)
        self.active = {s: 0 for s in self.servers}

    def choose(self, candidates):
        raise NotImplementedError


class PowerOfTwoChoices(LeastConnections):
    """Samples two healthy servers with rng.sample(candidates, 2) and sends
    the request to the less busy one."""

    def __init__(self, servers, rng, max_failures=3):
        super().__init__(servers, max_failures)
        self.rng = rng

    def choose(self, candidates):
        raise NotImplementedError


# --- 3. An API gateway -------------------------------------------------------


class Gateway:
    """routes: {path prefix: Balancer}. api_keys: the valid bearer tokens."""

    def __init__(self, routes, api_keys):
        self.routes = dict(routes)
        self.api_keys = set(api_keys)

    def handle(self, path, headers):
        """Return (status, server): (200, server) for an authenticated request
        to a routed path, or (401, None), (404, None), or (503, None)."""
        raise NotImplementedError
