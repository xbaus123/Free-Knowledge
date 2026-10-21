"""Networking basics: IP addresses, TCP's receive side, a caching DNS
resolver, and the arithmetic of latency and throughput."""


# --- 1. IP addresses -------------------------------------------------------


def ip_to_int(address):
    parts = address.split(".")
    if len(parts) != 4 or not all(p.isdigit() and int(p) <= 255 for p in parts):
        raise ValueError(f"not an IPv4 address: {address!r}")
    n = 0
    for p in parts:
        n = n * 256 + int(p)
    return n


def in_subnet(address, cidr):
    network, _, bits = cidr.partition("/")
    prefix = int(bits)
    if not 0 <= prefix <= 32:
        raise ValueError(f"bad prefix length in {cidr!r}")
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    return ip_to_int(address) & mask == ip_to_int(network) & mask


# --- 2. TCP's receive side -------------------------------------------------


class Receiver:
    def __init__(self):
        self.data = b""
        self._early = {}  # seq -> payload: segments that arrived before a gap was filled

    def receive(self, seq, payload):
        if len(payload) > len(self._early.get(seq, b"")):
            self._early[seq] = payload
        progressed = True
        while progressed:
            progressed = False
            for start, chunk in list(self._early.items()):
                end = start + len(chunk)
                if end <= len(self.data):  # nothing new: a duplicate
                    del self._early[start]
                elif start <= len(self.data):  # fills the gap, maybe overlapping
                    self.data += chunk[len(self.data) - start :]
                    del self._early[start]
                    progressed = True
        return len(self.data)


# --- 3. DNS ----------------------------------------------------------------


class Resolver:
    def __init__(self, network):
        self.network = network
        self.answers = {}  # name -> (record, expires_at): A and CNAME records
        self.zones = {}  # zone -> (server, expires_at): referrals

    def resolve(self, name, now):
        for _ in range(8):  # follow a few aliases, but never loop forever
            record = self._lookup(name, now)
            if record is None:
                return None
            if record["type"] == "A":
                return record["value"]
            name = record["value"]  # a CNAME: look up its target
        return None

    def _lookup(self, name, now):
        cached = self.answers.get(name)
        if cached and now < cached[1]:
            return cached[0]
        server = self._closest_server(name, now)
        while True:
            reply = self.network.query(server, name)
            if reply is None:
                return None
            if reply["type"] == "NS":
                self.zones[reply["zone"]] = (reply["value"], now + reply["ttl"])
                server = reply["value"]
                continue
            self.answers[name] = (reply, now + reply["ttl"])
            return reply

    def _closest_server(self, name, now):
        best, server = "", "root"
        for zone, (ns, expires) in self.zones.items():
            inside = name == zone or name.endswith("." + zone)
            if inside and now < expires and len(zone) > len(best):
                best, server = zone, ns
        return server


# --- 4. Latency and throughput ---------------------------------------------


def transfer_ms(size_bytes, bandwidth_mbps, rtt_ms, new_connection=True, tls=False):
    round_trips = 1  # the request and the response
    if new_connection:
        round_trips += 1  # TCP handshake
        if tls:
            round_trips += 1  # TLS 1.3 handshake
    return round_trips * rtt_ms + size_bytes * 8 / (bandwidth_mbps * 1000)


def max_throughput_mbps(window_bytes, rtt_ms):
    return window_bytes * 8 / (rtt_ms * 1000)


def bandwidth_delay_product(bandwidth_mbps, rtt_ms):
    return bandwidth_mbps * rtt_ms * 125
