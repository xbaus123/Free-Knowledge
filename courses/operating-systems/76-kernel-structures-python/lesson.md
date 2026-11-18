# Kernel Data Structures in Python

*Chapter 1 · Part 6: Protection, Security, and Kernel Data Structures.*

Two of the structures from this part, built by hand: a **bitmap** for tracking free items, and a **binary search tree** that shows why balance matters.

## Part 1: a bitmap

`Bitmap(n)` tracks the status of `n` items (numbered `0` to `n − 1`), all free to start with. Store the bits in **one Python integer**: bit *i* of the integer is item *i*. You'll need bit operations:

- Test bit *i*: `(bits >> i) & 1`
- Set bit *i*: `bits | (1 << i)`
- Clear bit *i*: `bits & ~(1 << i)`

Implement:

- `is_used(i)`, `use(i)`, `free(i)`. Raise `IndexError` if `i` is outside `0` to `n − 1`.
- `allocate()`: find the **first free item** (the lowest 0 bit), mark it used, and return its number. Return `-1` if everything is in use. This is how a kernel hands out free disk blocks or process IDs.
- `count_used()`: how many items are in use.
- `__str__()`: the bits as a string of `0`s and `1`s, **item 0 first**. `str(b)` for 10 items with 2, 4, 5, and 8 in use is `"0010110010"`.

## Part 2: a binary search tree

A `Node` class is given: `key`, `left`, `right`. Implement:

- `insert(root, key)`: insert `key` and return the root (a new `Node` if `root` is `None`). Smaller keys go left; keys **greater than or equal** go right.
- `search_steps(root, key)`: how many nodes you visit to find `key`, starting at the root and counting the node where you find it. If `key` isn't in the tree, return the number of nodes visited before falling off the bottom.
- `height(root)`: the number of nodes on the longest path from the root down. An empty tree has height `0`; a single node has height `1`.
- `build(keys)`: insert the keys in order into an empty tree and return the root.

The tests check the lesson's claim: the example tree (17, 12, 35, 6, 14, 32, 40, in that order) has height 3, but the same keys inserted in sorted order have height 7.

Use **Run** to try things out, and **Submit** to run the tests.
