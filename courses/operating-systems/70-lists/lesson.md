# Kernel Data Structures: Lists

*Chapter 1 · Part 6: Protection, Security, and Kernel Data Structures.*

The kernel juggles thousands of processes, files, memory blocks, and devices. To keep track of them, it uses data structures, and **many are similar to standard programming data structures** you may already know. The most common: **lists**.

## Singly linked list

Each item points to its **successor**. The last item points to **null**.

```
 [data|•]──►[data|•]──►[data|•]──► ... ──►[data|null]
```

## Doubly linked list

Each item points to **both its predecessor and its successor**. The first item's predecessor and the last item's successor are **null**.

```
 null◄──[•|data|•]◄──►[•|data|•]◄──►[•|data|•]──►null
```

You can walk it in either direction, and remove an item you already hold without searching for the one before it.

## Circular linked list

The **last item points back to the first**, so there's no null. Walking it goes round and round, which is perfect for **taking turns**: a scheduler can cycle through ready processes forever.

```
 ┌──►[data|•]──►[data|•]──►[data|•]──┐
 └───────────────────────────────────┘
```

Linux defines its list structures in `<linux/list.h>`.

Next, a check on lists.
