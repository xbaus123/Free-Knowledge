# Kernel Data Structures: Hash Maps and Bitmaps

*Chapter 1 · Part 6: Protection, Security, and Kernel Data Structures.*

Trees find things in O(lg *n*). Can we do better? With a **hash function**, often yes.

## Hash functions and hash maps

A **hash function** takes data as input, performs a numeric operation on it, and returns a **number**. That number is used as an **index into a table** to find the data.

```
              hash_function(key)
                     │
                     ▼
  ┌────┬────┬────┬────┬────┬────┐
  │ 0  │ 1  │ .  │    │ .  │ n  │   hash map
  └────┴────┴────┴──┬─┴────┴────┘
                    ▼
                 [ value ]
```

A **hash map** uses a hash function to associate **[key : value]** pairs. Give it a key, hash the key, and jump straight to the slot holding its value. Looking up a username to find its password data, for example, takes one hash and one look: **O(1)** on average, however many users there are.

## Bitmaps

A **bitmap** is a **string of *n* binary digits representing the status of *n* items**. Bit *i* is 0 or 1 to say whether item *i* is available or in use.

```
  bitmap:  0 0 1 0 1 1 0 0 1 0
  item:    0 1 2 3 4 5 6 7 8 9
```

Here, items 2, 4, 5, and 8 are in use (1), and the rest are free (0).

Bitmaps are tiny: tracking **1 million disk blocks takes only 1 million bits**, about **122 KB**. Finding a free item means finding the first 0 bit.

## Linux

Linux defines its data structures in include files such as:

| File | Structure |
|---|---|
| `<linux/list.h>` | Linked lists |
| `<linux/kfifo.h>` | A FIFO queue |
| `<linux/rbtree.h>` | Red-black (balanced) trees |

Next, a check on hash maps and bitmaps.
