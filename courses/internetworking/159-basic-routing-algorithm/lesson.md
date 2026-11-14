# The Basic Routing Algorithm

*Chapter 6 · Routing.*

When a packet arrives, how does a router decide where it goes? Underneath every implementation is the same short list of checks, tried **in order**:

```
get the packet's destination address
extract the destination network
  if it's on a network one of my interfaces is attached to   → deliver it on that local network
  else if a static route matches                             → forward via the static route
  else if the packet carries a source route                  → forward to the next hop it names
  else if my routing table has an entry                      → forward to that entry's next hop
  else                                                       → use the default route
```

## Each step

1. **Directly connected.** If the destination is on one of the router's own networks, there's no next router: ARP for the host and deliver the frame (chapter 4).
2. **Static route.** A route an administrator typed in by hand: "to reach 10.9.0.0/16, send to 10.1.1.2." Static routes never change by themselves.
3. **Source route.** The **sender** listed the path in the packet (an IP option). Rare today, and usually **blocked**: letting the sender choose the path lets an attacker steer traffic around your firewall.
4. **Routing table.** Routes learned **dynamically** from other routers by a routing protocol. Most of this chapter is about how those get built.
5. **Default route.** If nothing else matches, send it to the **default gateway**, usually written `0.0.0.0/0`: "everything else goes upstream." Your laptop's whole routing table is little more than its own network plus a default route.

## Static vs dynamic

| | Static routes | Dynamic routes |
|---|---|---|
| Set by | An administrator, by hand | A routing protocol, automatically |
| When a link fails | Nothing changes until someone fixes it | Routers find a new path |
| Best for | Small networks, a single exit to the ISP | Anything with redundant paths |
| Risk | Typos, forgotten routes | Trusting what neighbors tell you |

In practice, routers put all of these into one table and pick among them by **longest prefix match**, the topic of the next reading.

Next, a check on the routing algorithm.
