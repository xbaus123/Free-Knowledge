# Project: Plan Your Router

*Chapter 6 · Routing.*

Chapter 5 gave your project network its subnets. Now decide how the router connects them, and what it allows between them.

## The questions

**1. Which intra-domain routing protocol will you use?**

| Your network | A good fit |
|---|---|
| One router, one ISP connection | **Static routes** plus a static default route. No protocol needed |
| A few routers, simple layout | **RIP** (v2) is easy, but slow to converge and capped at 15 hops |
| Several routers, redundant links, room to grow | **OSPF**: fast convergence, classless, scales with areas |

You won't need BGP unless you're multi-homed with your own ASN.

**2. How many interfaces does the router need?**
One per subnet it routes between (or one trunk link to the switch carrying all the VLANs, with a **subinterface per VLAN**: a setup nicknamed "router on a stick"), plus the **uplink** to the ISP or firewall. Leave a spare.

**3. How will you configure it?**
- Gateway address on each interface: the **first usable** address of each subnet, as in chapter 5.
- **Passive interfaces** on every user-facing subnet; routing hellos only on router-to-router links.
- **Authentication** (HMAC-SHA) on every routing neighbor.
- Management (SSH only) from the admin subnet only. Log routing changes.

**4. Will you have ACLs? What rules?**
Yes. Write them in plain language first, most specific first, and end with **deny everything else**.

## A worked example

The chapter 5 office, one router with a trunk to the core switch and an uplink to the firewall:

| Interface | Subnet | Gateway | Routing |
|---|---|---|---|
| Gi0/0.10 | Staff 192.168.10.0/25 | .1 | Passive |
| Gi0/0.20 | Guests 192.168.10.128/26 | .129 | Passive |
| Gi0/0.30 | Cameras 192.168.10.192/27 | .193 | Passive |
| Gi0/0.40 | Servers 192.168.10.224/28 | .225 | Passive |
| Gi0/1 | Link to firewall 192.168.10.240/30 | .241 | Static default via .242 |

One router and one exit, so **static routes** are enough; if a second site is added later, switch to OSPF.

ACL rules, in order:

1. Staff → servers: **allow** the ports the apps need (443, 445).
2. Guests → any 192.168.10.0/24 address: **deny**. Guests → Internet: allow.
3. Cameras → the recording server only: **allow**. Cameras → Internet: **deny**.
4. Any source address that doesn't belong to its subnet: **deny** (ingress filtering).
5. Everything else: **deny**.

## Questions your write-up should answer

- Which routing protocol did you choose, and why not the others?
- How many interfaces does your router have, and which subnet is on each?
- What ACL rules does it have, in order? What's the default?
- How is the router itself protected (management access, authentication, logging)?

Next, a check on planning your router.
