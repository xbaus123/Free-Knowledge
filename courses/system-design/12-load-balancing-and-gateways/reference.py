"""Load balancing algorithms, passive health checks, and an API gateway."""


class NoHealthyServers(Exception):
    pass


# --- 1. Health ---------------------------------------------------------------


class Balancer:
    """Shared by every algorithm: tracks which servers are healthy."""

    def __init__(self, servers, max_failures=3):
        self.servers = list(servers)
        self.max_failures = max_failures
        self.failures = {s: 0 for s in self.servers}  # consecutive failures
        self.down = set()

    def healthy(self):
        return [s for s in self.servers if s not in self.down]

    def report(self, server, ok):
        if ok:
            self.failures[server] = 0
            return
        self.failures[server] += 1
        if self.failures[server] >= self.max_failures:
            self.down.add(server)

    def mark_up(self, server):
        self.down.discard(server)
        self.failures[server] = 0

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
        # Walk the full list so a server coming back keeps its place.
        while True:
            server = self.servers[self.next % len(self.servers)]
            self.next += 1
            if server in candidates:
                return server


class WeightedRoundRobin(Balancer):
    """Smooth weighted round robin, as in NGINX."""

    def __init__(self, weights, max_failures=3):
        super().__init__(weights, max_failures)
        self.weights = dict(weights)
        self.current = {s: 0 for s in self.servers}

    def choose(self, candidates):
        total = 0
        best = None
        for s in candidates:
            self.current[s] += self.weights[s]
            total += self.weights[s]
            if best is None or self.current[s] > self.current[best]:
                best = s
        self.current[best] -= total
        return best


class LeastConnections(Balancer):
    def __init__(self, servers, max_failures=3):
        super().__init__(servers, max_failures)
        self.active = {s: 0 for s in self.servers}

    def choose(self, candidates):
        server = min(candidates, key=lambda s: self.active[s])  # ties: list order
        self.active[server] += 1
        return server

    def release(self, server):
        self.active[server] -= 1


class PowerOfTwoChoices(LeastConnections):
    def __init__(self, servers, rng, max_failures=3):
        super().__init__(servers, max_failures)
        self.rng = rng

    def choose(self, candidates):
        if len(candidates) == 1:
            server = candidates[0]
        else:
            a, b = self.rng.sample(candidates, 2)
            server = b if self.active[b] < self.active[a] else a
        self.active[server] += 1
        return server


# --- 3. An API gateway -------------------------------------------------------


class Gateway:
    def __init__(self, routes, api_keys):
        self.routes = dict(routes)  # path prefix -> Balancer
        self.api_keys = set(api_keys)

    def handle(self, path, headers):
        auth = headers.get("Authorization", "")
        scheme, _, token = auth.partition(" ")
        if scheme != "Bearer" or token not in self.api_keys:
            return 401, None
        prefix = self.match(path)
        if prefix is None:
            return 404, None
        try:
            return 200, self.routes[prefix].pick()
        except NoHealthyServers:
            return 503, None

    def match(self, path):
        best = None
        for prefix in self.routes:
            p = prefix.rstrip("/")
            if path == p or path.startswith(p + "/") or p == "":
                if best is None or len(p) > len(best.rstrip("/")):
                    best = prefix
        return best
