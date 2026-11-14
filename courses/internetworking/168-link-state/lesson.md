# Link State Routing

*Chapter 6 · Routing.*

Link state takes the opposite approach: instead of trusting a neighbor's summary, every router gets the **raw facts** and works out the answer itself.

## How it works

1. **Meet the neighbors.** Each router sends small *hello* messages to discover its neighbors and form **adjacencies**.
2. **Flood your links.** Each router describes its own links and their costs in a **link state advertisement (LSA)** and sends it to everyone. Every router passes each new LSA on, **reliably** (with acknowledgments), so all routers get every LSA.
3. **Build the map.** Every router now has the **same** complete picture of the network: the **link state database**.
4. **Compute.** Each router runs **Dijkstra's shortest path algorithm** with itself as the root, and turns the result into its forwarding table.
5. **Update on change.** LSAs are sent again only when something **changes** (plus an occasional refresh), so a failure spreads in seconds.

## Dijkstra, worked out

Same network as before:

```
         1          5          3
    A ──────── B ──────── D ──────── E
     \         │         /
    4 \      2 │        / 1
       \       │       /
        └───── C ─────┘
```

Links: A–B 1, A–C 4, B–C 2, B–D 5, C–D 1, D–E 3.

Start at A. Repeatedly pick the closest router you haven't finalized, then see if going through it shortens any path:

| Step | Finalize | Cost | Via | Updates to others |
|---|---|---|---|---|
| 1 | A | 0 | | B = 1, C = 4 |
| 2 | B | 1 | B | C = min(4, 1 + 2) = **3**, D = 1 + 5 = 6 |
| 3 | C | 3 | B | D = min(6, 3 + 1) = **4** |
| 4 | D | 4 | B | E = 4 + 3 = 7 |
| 5 | E | 7 | B | |

Every destination's first hop from A is **B**. Same answers distance vector reached, but A computed them from the full map instead of from rumors.

## OSPF and IS-IS

**OSPF (Open Shortest Path First)** is the most common link state protocol inside organizations. **IS-IS** does the same job and is popular with large ISPs. To scale, both split a big network into **areas**: a router knows every link in its own area (that's the asterisk on "every router knows the whole graph") and only summaries of the others.

Next, a check on link state routing.
