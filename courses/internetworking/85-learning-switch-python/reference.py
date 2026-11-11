"""A learning switch, and the spanning tree's root election and path costs."""

BROADCAST = "ff:ff:ff:ff:ff:ff"

# Classic 802.1D link costs, by link speed in Mbps.
STP_COST = {10: 100, 100: 19, 1000: 4, 10000: 2}


class LearningSwitch:
    def __init__(self, ports):
        self.ports = sorted(ports)
        self.table = {}

    def receive(self, in_port, src, dst):
        src, dst = src.lower(), dst.lower()
        self.table[src] = in_port
        out = self.table.get(dst)
        if dst == BROADCAST or out is None:
            return [p for p in self.ports if p != in_port]
        if out == in_port:
            return []
        return [out]

    def forget(self, mac):
        self.table.pop(mac.lower(), None)


def bridge_id(priority, mac):
    return (priority << 48) | int(mac.replace(":", ""), 16)


def elect_root(bridges):
    if not bridges:
        return None
    return min(bridges, key=lambda name: bridge_id(*bridges[name]))


def path_cost(speeds):
    return sum(STP_COST[s] for s in speeds)


def root_port(paths):
    if not paths:
        return None
    return min(sorted(paths), key=lambda port: path_cost(paths[port]))
