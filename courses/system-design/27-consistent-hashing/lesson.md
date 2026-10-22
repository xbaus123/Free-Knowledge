# Consistent Hashing: A Partitioner That Scales

Your cache cluster has 10 nodes, and a `Partitioner` decides which node stores each key. The current one uses the obvious rule:

```python
node = nodes[hash(key) % len(nodes)]
```

It spreads keys evenly. But traffic is growing and you're about to add an 11th node. With `% 10` becoming `% 11`, almost every key's home changes. **About 90% of the cache misses at once**, and all that traffic falls through to the database. That's a thundering herd you caused yourself.

## Your task

Rewrite `Partitioner` as a **consistent hash ring** with **virtual nodes**:

1. Hash every node name onto a ring of 64-bit integers, **many times** each: `stable_hash(f"{node}#{i}")` for i in `range(vnodes)`. Keep the points in a **sorted** list of `(point, node)`.
2. A key belongs to the first point **clockwise** from its hash, wrapping around to the start of the list past the end.
3. Adding a node inserts its points. It takes over only the arcs just before each of its points, and nothing else moves.
4. Removing a node deletes its points. Its keys fall to the next points clockwise, which belong to many different nodes, so the load spreads out.

The grader feeds **10,000 keys** through your partitioner and checks that:

- Keys spread **evenly**: every node is within ±25% of the average.
- Adding an 11th node moves **at most 1/N** of the keys (1,000), all of them to the new node.
- Removing a node moves only that node's keys, with no single node absorbing more than 30% of them, and adding it back restores the original placement.
- Placement is the same in **every process**. Python's built-in `hash()` of a string is randomized per process, so use `stable_hash` (MD5).
- Lookups use **binary search** (`bisect`). 10,000 lookups on a 50-node ring must take well under a second.

```python
import bisect
points = [10, 20, 30]
bisect.bisect_right(points, 25)   # 2: the index of the first point > 25
```

Use the **Scratchpad** to experiment: your code is importable there as `solution`. How uneven does the distribution get with `vnodes=1`? With 10? With 200?

```python
from collections import Counter
from solution import Partitioner

p = Partitioner([f"node-{i}" for i in range(10)], vnodes=1)
print(Counter(p.node_for(f"user:{i}") for i in range(10_000)))
```

## Think about it

- Why do virtual nodes improve *both* the balance and how removed load is spread?
- Give a powerful machine more virtual nodes than a small one, and it takes a proportionally bigger share. That's **weighted** consistent hashing.
- Databases like Riak and Elasticsearch instead create a **fixed number of partitions** up front and move whole partitions between nodes. What does that make easier?
