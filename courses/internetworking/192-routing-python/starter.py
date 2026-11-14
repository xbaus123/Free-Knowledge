"""A router's brain: longest prefix match, Dijkstra, distance vector, and BGP checks."""

ALL_ONES = 0xFFFFFFFF
INFINITY = 16  # RIP's "unreachable"


# ---------------------------------------------------------------------------
# Helpers, done for you.


def ip_to_int(text):
    a, b, c, d = (int(part) for part in text.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def mask(prefix):
    """The mask for a prefix length, as a 32-bit integer."""
    return (ALL_ONES << (32 - prefix)) & ALL_ONES


def parse_cidr(cidr):
    """"10.1.2.0/24" -> (ip_to_int("10.1.2.0"), 24)."""
    ip, prefix = cidr.split("/")
    return ip_to_int(ip), int(prefix)


# ---------------------------------------------------------------------------
# Part 1: forwarding


def lookup(table, destination):
    """Longest prefix match.

    table is a list of (cidr, next_hop), in any order. Return the next_hop of
    the longest prefix that matches the destination address (a dotted-decimal
    string), or None if nothing matches. "0.0.0.0/0" matches everything.

    A destination matches a prefix when the first `prefix` bits are equal:
    dst & mask(prefix) == net & mask(prefix)
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 2: link state


def dijkstra(graph, source):
    """Shortest paths from source.

    graph maps each router to {neighbor: link_cost}. Return
    {destination: (cost, first_hop)} for every router you can reach,
    not including source itself. first_hop is the neighbor of source that
    the path starts through.

    dijkstra(GRAPH, "A")["D"] == (4, "B")
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 3: distance vector


def dv_update(me, links, vectors):
    """One Bellman-Ford update for router `me`.

    links maps each neighbor to the cost of the link to it.
    vectors maps each neighbor to the distance vector it last sent:
    {destination: cost}. A neighbor might not have sent one yet.

    Return {destination: (cost, next_hop)}:
    - every neighbor is reachable over its link (a neighbor's cost to itself is 0)
    - skip `me`
    - leave out anything that costs INFINITY (16) or more
    - on a tie, pick the neighbor whose name sorts first
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 4: path vector and BGP security


def accept_path(my_asn, as_path):
    """False if my_asn is already in as_path (accepting it would make a loop)."""
    # TODO
    pass


def prepend(my_asn, as_path):
    """The path to pass on: my_asn added to the front. Don't change as_path."""
    # TODO
    pass


def origin_validate(roas, prefix, origin_asn):
    """RPKI route origin validation.

    roas is a list of (roa_prefix, max_length, asn). A ROA covers an announced
    prefix when the prefix lies inside the ROA's prefix (it's at least as long,
    and its first roa-length bits match).

    Return "valid" if some covering ROA has the same asn and the announced
    length is <= its max_length; "invalid" if ROAs cover it but none match;
    "not found" if no ROA covers it.
    """
    # TODO
    pass


if __name__ == "__main__":
    table = [("200.23.16.0/21", 0), ("200.23.24.0/24", 1), ("200.23.24.0/21", 2), ("0.0.0.0/0", 3)]
    print(lookup(table, "200.23.24.170"))          # 1

    graph = {
        "A": {"B": 1, "C": 4},
        "B": {"A": 1, "C": 2, "D": 5},
        "C": {"A": 4, "B": 2, "D": 1},
        "D": {"B": 5, "C": 1, "E": 3},
        "E": {"D": 3},
    }
    print(dijkstra(graph, "A"))                    # every first hop is B

    print(origin_validate([("203.0.113.0/24", 25, 64500)], "203.0.113.128/25", 64999))  # invalid
