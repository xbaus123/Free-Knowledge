# Exam 3 Review: Routing and ASNs

*Chapter 9 · Upper Layers.*

The next four lessons are a review for **exam 3**: a **60 minute** exam on routing, DNS, mail, and this chapter's session and application layers. This first pair picks up the routing material: a few more routing questions, **IP to ASN** mapping, and very simple questions about **RIP**, **OSPF**, and the others.

## Routing protocols in one table

| Protocol | Type | Where | Remember |
|---|---|---|---|
| **RIP** | **Distance vector** | Inside an AS | Metric is **hop count**, **15 hops** max (16 = unreachable), slow to converge |
| **OSPF** | **Link state** | Inside an AS | Every router learns the whole map (of its **area**), runs Dijkstra, converges fast |
| **IS-IS** | Link state | Inside an AS | Like OSPF, popular with big ISPs |
| **BGP** | **Path vector** | **Between** ASes | Carries the list of ASes a route passes through, to avoid loops and apply policy |

- **Intra-domain** (inside one AS): RIP, OSPF, IS-IS. Goal: **performance**.
- **Inter-domain** (between ASes): BGP. Goal: **policy**.

## Autonomous systems and IP to ASN

An **autonomous system** is a network under one administration with one routing policy, identified by an **ASN**. Every public prefix is **announced** in BGP by some AS, so you can map an address to the AS that owns it:

| Address | ASN | Who |
|---|---|---|
| 8.8.8.8 | AS15169 | Google |
| 1.1.1.1 | AS13335 | Cloudflare |

Tools: an **IP to ASN** lookup site, or `whois` on the address (look for `OriginAS`). Run the lookup on each hop of a `traceroute` and you can watch a packet cross from one AS to the next.

## Longest prefix match

A router picks the route with the **longest** matching prefix. With routes for `10.0.0.0/8` and `10.1.0.0/16`, a packet to `10.1.2.3` takes the `/16`. A packet to `10.9.9.9` only matches the `/8`. `0.0.0.0/0` (the default route) matches everything, so it's the last resort.

Next, a drill on routing and ASNs.
