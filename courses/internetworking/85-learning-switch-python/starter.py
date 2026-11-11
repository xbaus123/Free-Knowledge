"""A learning switch, and the spanning tree's root election and path costs."""

BROADCAST = "ff:ff:ff:ff:ff:ff"

# Classic 802.1D link costs, by link speed in Mbps.
STP_COST = {10: 100, 100: 19, 1000: 4, 10000: 2}


# ---------------------------------------------------------------------------
# Part 1: the learning switch


class LearningSwitch:
    def __init__(self, ports):
        """ports is a list of port numbers, such as [1, 2, 3, 4]."""
        self.ports = sorted(ports)
        self.table = {}  # MAC address -> port number

    def receive(self, in_port, src, dst):
        """A frame from src to dst arrived on in_port.

        1. Learn: remember that src is reachable through in_port.
        2. Return the list of ports to send the frame out of:
           - dst is the broadcast address, or not in the table yet:
             flood, every port except in_port, in increasing order
           - dst is in the table on in_port itself: filter, []
           - otherwise: [the port dst was learned on]
        MAC addresses may arrive in upper or lower case: store and
        compare them in lower case.
        """
        # TODO
        pass

    def forget(self, mac):
        """Age out one entry. Do nothing if mac isn't in the table."""
        # TODO
        pass


# ---------------------------------------------------------------------------
# Part 2: spanning tree


def bridge_id(priority, mac):
    """The bridge ID as one number: the priority, then the 48-bit MAC.

    Shift the priority left 48 bits and OR in the MAC as an integer, so
    comparing two IDs compares priorities first and MACs only on a tie.
    bridge_id(32768, "00:00:00:00:00:01") == 32768 * 2**48 + 1
    """
    # TODO
    pass


def elect_root(bridges):
    """The name of the root bridge: the lowest bridge ID wins.

    bridges maps a name to (priority, mac):
        {"SW1": (32768, "00:00:00:00:0a:aa"), "SW2": (32768, "00:00:00:00:0b:bb")}
    Return None if there are no bridges.
    """
    # TODO
    pass


def path_cost(speeds):
    """Total STP cost of a path: the sum of STP_COST for each link speed."""
    # TODO
    pass


def root_port(paths):
    """Pick the root port: the one whose path to the root is cheapest.

    paths maps a port name to the link speeds (Mbps) on its path to the root:
        {"Fa0/0": [100], "Gi0/1": [1000, 1000]}  ->  "Gi0/1" (cost 8 beats 19)
    On a tie, the port name that sorts first wins. Return None for no ports.
    """
    # TODO
    pass


if __name__ == "__main__":
    sw = LearningSwitch([1, 2, 3, 4])
    print(sw.receive(1, "aa:aa:aa:aa:aa:aa", "cc:cc:cc:cc:cc:cc"))  # flood
    print(sw.receive(3, "cc:cc:cc:cc:cc:cc", "aa:aa:aa:aa:aa:aa"))  # forward to 1
    print(sw.table)
