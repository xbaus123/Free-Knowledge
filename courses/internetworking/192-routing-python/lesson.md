# A Router's Brain in Python

*Chapter 6 · Routing.*

Time to build the decisions this chapter described. Every function here uses an example from the readings or drills, so you can check your answers against them.

`ip_to_int`, `mask(prefix)`, and `parse_cidr` are already written for you at the top of the file.

## Part 1: longest prefix match

`lookup(table, destination)` walks the table and keeps the **longest** prefix that matches. A destination matches a prefix when its first *prefix* bits equal the network's:

```python
dst & mask(length) == net & mask(length)
```

The default route `0.0.0.0/0` has length 0, so `mask(0)` is 0 and it matches everything, but it loses to any longer match. A real router does this in one TCAM clock cycle; a loop is fine for us.

## Part 2: Dijkstra

`dijkstra(graph, source)` returns `{destination: (cost, first_hop)}`. Keep a set of finalized routers, and each round finalize the closest one you haven't finished. Python's `heapq` gives you "the closest" cheaply: push `(cost, router, first_hop)` and pop the smallest.

The **first hop** is the trick: when you step out of the source, the first hop is the neighbor itself. After that, every router reached inherits the first hop of the router it was reached through.

## Part 3: distance vector

`dv_update(me, links, vectors)` is one round of Bellman-Ford: for each destination, try every neighbor, cost = **link cost + neighbor's reported cost**, and keep the cheapest. Leave out anything at 16 or more (RIP's infinity). One of the tests replays the first step of **count to infinity**: your code will happily make the same mistake router B did.

## Part 4: path vector and RPKI

- `accept_path(my_asn, as_path)`: reject a path with your own AS in it.
- `prepend(my_asn, as_path)`: what you pass on to your neighbors.
- `origin_validate(roas, prefix, origin_asn)`: **valid**, **invalid**, or **not found**, like the BGP security drill.

Use **Run** to try things out, and **Submit** to run the tests.
