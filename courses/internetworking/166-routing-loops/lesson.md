# Routing Loops and RIP

*Chapter 6 · Routing.*

Distance vector routers believe their neighbors. Usually that's fine. When a link **fails**, it can go badly wrong.

## Count to infinity

Three routers in a line, every link cost 1:

```
 A ──── B ──── C
```

A reaches C at cost 2, through B. Now the **B–C link fails**.

| Step | What happens | B's cost to C | A's cost to C |
|---|---|---|---|
| 0 | Before the failure | 1 (direct) | 2 (via B) |
| 1 | B loses its link, then hears A say "I reach C at 2" | 3 (via A!) | 2 |
| 2 | A hears B's new cost and updates | 3 | 4 (via B) |
| 3 | B hears A's new cost | 5 | 4 |
| … | Bad news crawls up one step at a time | … | … |

A's "cost 2" route went **through B**, but B doesn't know that. Each believes the other has a way to C. Packets for C bounce between them, a **routing loop**, while the costs creep upward forever. That's the **count-to-infinity problem**.

## Three fixes

- **Define infinity small.** RIP treats a cost of **16** as unreachable, so the count stops quickly. The price: no RIP network can be more than **15 hops** across.
- **Split horizon.** Never advertise a route back out the interface you learned it from. A learned its route to C from B, so it doesn't tell B about it. B finds no route and correctly marks C unreachable.
- **Poison reverse.** Go one step further: advertise that route back to B **with cost infinity**: "Don't come through me for C."

## RIP in one table

| | RIP (Routing Information Protocol) |
|---|---|
| Family | Distance vector |
| Metric | Hop count |
| Maximum | 15 hops; 16 means unreachable |
| Updates | Every **30 seconds** (timer-based), plus triggered updates |
| Versions | RIPv1 is **classful**; RIPv2 carries masks, so it's classless |
| Good for | Small, simple networks: it's easy to set up |

Distance vector is cheap on CPU and simple to configure, but it **converges slowly** and doesn't scale. Large networks use link state instead.

Next, a check on routing loops.
