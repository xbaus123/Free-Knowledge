"""Networking basics: IP addresses, TCP's receive side, a caching DNS
resolver, and the arithmetic of latency and throughput.

Four independent parts. The lesson explains each one; the tests check
them separately, so you can finish them in any order.
"""


# --- 1. IP addresses -------------------------------------------------------


def ip_to_int(address):
    """'192.168.1.10' -> 3232235786: the address as one 32-bit number.

    Raise ValueError for anything that isn't four numbers from 0 to 255
    separated by dots.
    """
    raise NotImplementedError


def in_subnet(address, cidr):
    """Is address inside the CIDR block? in_subnet('10.1.2.3', '10.0.0.0/8') -> True.

    The number after the slash is how many leading bits must match.
    """
    raise NotImplementedError


# --- 2. TCP's receive side -------------------------------------------------


class Receiver:
    """Turns segments that arrive late, twice, or out of order back into
    the exact byte stream the sender wrote."""

    def __init__(self):
        self.data = b""  # bytes delivered to the application, in order

    def receive(self, seq, payload):
        """A segment arrived: payload starts at byte number seq of the stream.

        Deliver every byte you can into self.data, keep segments that
        arrived early until the gap before them is filled, and ignore bytes
        you already have. Return the cumulative ACK: the number of the next
        byte you're waiting for.
        """
        raise NotImplementedError


# --- 3. DNS ----------------------------------------------------------------


class Resolver:
    """A caching DNS resolver.

    network.query(server, name) asks one name server about one name and
    returns one of:

      {"type": "A", "value": "93.184.216.34", "ttl": 300}       the address
      {"type": "CNAME", "value": "edge.cdn.net", "ttl": 60}      an alias: resolve value instead
      {"type": "NS", "zone": "com", "value": "tld-com", "ttl": 172800}
                                                                 a referral: ask server value,
                                                                 which knows names in zone
      None                                                       no such name

    Every lookup without a usable cache entry starts at the server "root".
    """

    def __init__(self, network):
        self.network = network

    def resolve(self, name, now):
        """Return the IPv4 address for name, or None if it doesn't exist.

        now is the current time in seconds. Cache A and CNAME answers, and
        NS referrals, until now + ttl; at that moment they've expired. Start
        each lookup at the closest server you know: the one for the longest
        cached zone that name falls in.
        """
        raise NotImplementedError


# --- 4. Latency and throughput ---------------------------------------------


def transfer_ms(size_bytes, bandwidth_mbps, rtt_ms, new_connection=True, tls=False):
    """How long an HTTP request takes until the last byte of the response arrives.

    One round trip for the request and response, plus one for the TCP
    handshake on a new connection, plus one more for TLS (1.3) on a new
    connection. Then the response's transmission time at bandwidth_mbps
    (1 Mbit/s = 1,000,000 bits per second). Ignore everything else.
    """
    raise NotImplementedError


def max_throughput_mbps(window_bytes, rtt_ms):
    """The fastest a sender can go when it may have at most window_bytes
    unacknowledged, and each acknowledgment takes a round trip to arrive."""
    raise NotImplementedError


def bandwidth_delay_product(bandwidth_mbps, rtt_ms):
    """How many bytes are in flight when a link is kept full for one round trip."""
    raise NotImplementedError
