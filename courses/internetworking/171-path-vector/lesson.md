# Path Vector Routing

*Chapter 6 · Routing.*

The third family is an **extension of distance vector**. Routers still talk only to neighbors, but instead of advertising "I can reach this network at cost 4," they advertise **the whole path**:

> "I can reach 203.0.113.0/24 through networks **X → Y → Z**."

## What the path buys you

**1. Loop detection for free.** When a router receives a path, it checks whether **its own name is already in it**. If so, accepting it would create a loop, so it's thrown away. No count to infinity.

```
 Y advertises to X:  "203.0.113.0/24 via Y, Z"     ✓ X isn't in the path: accept
 Z advertises to X:  "203.0.113.0/24 via Z, Y, X"  ✗ X is already in it: reject
```

**2. Policy.** With the full path in hand, a router can choose by **rules**, not just by distance:

- "Never send our traffic through network W."
- "Prefer the path through our paying customer over the one through our competitor."
- "Don't tell network V about routes we learned from network U."

A shortest-path protocol can't express any of that. Path vector **adapts to policies**.

## Where it's used

The names in the path aren't individual routers: they're whole **networks run by different organizations**, called **autonomous systems**. The path vector protocol that connects them is **BGP**, the protocol that holds the Internet together. The next few readings cover autonomous systems and BGP.

Next, a check on path vector routing.
