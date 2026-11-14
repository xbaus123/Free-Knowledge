# BGP: The Internet's Routing Protocol

*Chapter 6 · Routing.*

The **Border Gateway Protocol (BGP)** is the path vector protocol that connects every AS. BGP routing tables are what make the Internet one network instead of 75,000 separate ones.

## The basics

- BGP routers, called **speakers**, form **sessions** with each other over **TCP port 179**.
- Between ASes it's **eBGP** (external). Inside an AS, the border routers share what they learned using **iBGP** (internal).
- An announcement says: "this **prefix** is reachable through this **AS path**."

```
 AS 64500 announces 203.0.113.0/24, path [64500]
       │
       ▼
 AS 64501 adds itself:  203.0.113.0/24, path [64501 64500]
       │
       ▼
 AS 64502 adds itself:  203.0.113.0/24, path [64502 64501 64500]
```

## Propagation and convergence

- **Propagation**: each AS that accepts a route adds its own ASN to the front of the path and passes it on to its neighbors (if its policy says to). Within minutes, a new prefix is known across the world.
- **Convergence**: after a change, like a new prefix, a withdrawn one, or a failed link, routers swap updates until everyone settles on a stable choice again. BGP converges **slowly**: it can take **minutes**, and the global table holds around **a million** IPv4 prefixes.

## How BGP picks a route

When several neighbors offer a route to the same prefix, BGP doesn't just count. Roughly in order:

1. **Local preference**: the AS's own policy. Routes through a paying customer usually beat routes through a provider you pay.
2. **Shortest AS path**.
3. Then tie-breakers (which exit is closest inside the AS, and so on).

And before any of that, **longest prefix match** still applies when forwarding: a /24 beats a /22.

## The weakness: BGP believes what it hears

Plain BGP has **no built-in check** that an AS is allowed to announce a prefix. In **2008**, a Pakistani ISP announced a **/24** inside YouTube's **/22**, meant to block YouTube within Pakistan. The announcement leaked to the rest of the world. Because a /24 is more specific, routers everywhere preferred it, and YouTube went dark globally for about two hours. That's a **BGP hijack**, and it's why the next reading is about securing BGP.

Next, a check on BGP.
