# Kernel Data Structures: Trees

*Chapter 1 · Part 6: Protection, Security, and Kernel Data Structures.*

Lists are simple, but finding something in one means walking it item by item: O(*n*). When the kernel needs to find things fast among thousands, it uses **trees**.

## Binary search tree

A **binary search tree** (BST) keeps its items in order: for every node, **left ≤ right**. Everything in the left subtree is smaller than (or equal to) the node; everything in the right subtree is larger.

```
              17
            /    \
          12      35
         /  \    /  \
        6   14  32   40
```

To find 32: start at 17 (32 is bigger, go right), reach 35 (32 is smaller, go left), reach 32. **Three steps** instead of checking all seven nodes.

## The catch: O(*n*) in the worst case

A BST's **search performance is O(*n*)** in the worst case. Insert 6, 12, 14, 17, 32, 35, 40 **in sorted order** and every node goes to the right of the last one:

```
 6
  \
   12
     \
      14
        \
         ... 40
```

That's just a linked list in disguise: searching for 40 takes 7 steps.

## Balanced binary search tree: O(lg *n*)

A **balanced binary search tree** keeps itself short by rearranging nodes as items are added or removed. A tree with *n* items then has height about lg *n* (log base 2), so search is **O(lg *n*)**.

| Items (*n*) | Worst-case BST search | Balanced BST search |
|---|---|---|
| 7 | 7 steps | 3 steps |
| 1,000 | 1,000 | about 10 |
| 1,000,000 | 1,000,000 | about 20 |

Linux defines its balanced tree in `<linux/rbtree.h>`.

Next, a check on trees.
