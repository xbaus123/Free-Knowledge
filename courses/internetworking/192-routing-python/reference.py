"""A router's brain: longest prefix match, Dijkstra, distance vector, and BGP checks."""

import heapq

ALL_ONES = 0xFFFFFFFF
INFINITY = 16


def ip_to_int(text):
    a, b, c, d = (int(part) for part in text.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def mask(prefix):
    return (ALL_ONES << (32 - prefix)) & ALL_ONES


def parse_cidr(cidr):
    ip, prefix = cidr.split("/")
    return ip_to_int(ip), int(prefix)


def lookup(table, destination):
    dst = ip_to_int(destination)
    best, best_len = None, -1
    for cidr, hop in table:
        net, length = parse_cidr(cidr)
        if dst & mask(length) == net & mask(length) and length > best_len:
            best, best_len = hop, length
    return best


def dijkstra(graph, source):
    result = {}
    queue = [(0, source, None)]
    done = set()
    while queue:
        cost, node, first = heapq.heappop(queue)
        if node in done:
            continue
        done.add(node)
        if node != source:
            result[node] = (cost, first)
        for neighbor, link in graph.get(node, {}).items():
            if neighbor not in done:
                heapq.heappush(queue, (cost + link, neighbor, neighbor if node == source else first))
    return result


def dv_update(me, links, vectors):
    table = {}
    for neighbor in sorted(links):
        reported = dict(vectors.get(neighbor, {}))
        reported[neighbor] = 0
        for dest, cost in reported.items():
            if dest == me:
                continue
            total = links[neighbor] + cost
            if total >= INFINITY:
                continue
            if dest not in table or total < table[dest][0]:
                table[dest] = (total, neighbor)
    return table


def accept_path(my_asn, as_path):
    return my_asn not in as_path


def prepend(my_asn, as_path):
    return [my_asn] + list(as_path)


def origin_validate(roas, prefix, origin_asn):
    net, length = parse_cidr(prefix)
    covered = False
    for roa_prefix, max_length, asn in roas:
        roa_net, roa_len = parse_cidr(roa_prefix)
        if length >= roa_len and net & mask(roa_len) == roa_net:
            covered = True
            if asn == origin_asn and length <= max_length:
                return "valid"
    return "invalid" if covered else "not found"
