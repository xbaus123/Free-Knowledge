# A Learning Switch in Python

*Chapter 3 · The Data Link Layer.*

A switch's two big jobs are learning where every host is, and (with its neighbors) agreeing on a loop-free tree. You'll write both: the forwarding logic that runs for every frame, and the arithmetic of a spanning tree election.

## Part 1: the learning switch

For every frame that arrives, a switch:

1. **Learns** the frame's source MAC address on the port it came in on.
2. Looks up the destination MAC address:
   - the **broadcast** address, or **unknown**: **flood** it out of every port except the one it came in on
   - known, on the **same** port it came in on: **filter** it (send it nowhere)
   - known, on another port: **forward** it out of that one port

## Part 2: spanning tree

- A **bridge ID** is the priority followed by the MAC address. As one number: `(priority << 48) | mac_as_int`. Comparing two of those compares priorities first, and MAC addresses only on a tie, which is exactly the rule for electing the root. `int("0000000000ff", 16)` turns hex into an integer.
- A path's **cost** is the sum of each link's cost, from the classic table in `STP_COST`: 100 for 10 Mbps, 19 for 100 Mbps, 4 for 1 Gbps, 2 for 10 Gbps.
- A switch's **root port** is the port with the cheapest path to the root. (Real STP breaks ties by the neighbor's bridge ID and then port IDs; here, the port name that sorts first wins.)

## Your task

Implement these in the editor:

- `LearningSwitch.receive(in_port, src, dst)`: learn `src`, then return the list of ports to send the frame out of, as above. Flooded ports come in increasing order. MAC addresses may arrive in any case: store and compare them in lower case.
- `LearningSwitch.forget(mac)`: remove one entry from `self.table` (aging it out). Do nothing if it isn't there.
- `bridge_id(priority, mac)`: the bridge ID as one integer.
- `elect_root(bridges)`: `bridges` maps names to `(priority, mac)`. Return the name of the switch with the lowest bridge ID, or `None` for an empty dictionary.
- `path_cost(speeds)`: the total cost of a list of link speeds in Mbps.
- `root_port(paths)`: `paths` maps each port name to the list of link speeds on its path to the root. Return the cheapest port, the first by name on a tie, or `None` if there are no ports.

Use **Run** to try things out, and **Submit** to run the tests.
