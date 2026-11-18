# Caching

*Chapter 1 · Part 2: Computer-System Organization.*

The storage hierarchy has a problem: the fast storage is small, and the big storage is slow. **Caching** is how computers get most of the speed of the fast level with most of the size of the slow one.

## The idea

Information in use is **copied from slower storage into faster storage temporarily**. That faster storage is the **cache**. Then, whenever we need something:

1. **Check the cache first.**
2. If it's there (a **cache hit**), use it directly from the cache. Fast.
3. If not (a **cache miss**), copy the data from the slower storage into the cache, and use it there.

## Caching everywhere

Caching is an important principle performed at **many levels** in a computer: in hardware, in the operating system, and in software.

- The **CPU cache** caches main memory.
- **Main memory** can be viewed as a **cache for secondary storage**: the OS keeps recently used file blocks in memory.
- Your **web browser** caches pages and images from the network.

## The hard part: it doesn't all fit

The cache is **smaller than the storage being cached**, so **cache management** is an important design problem:

- **Cache size**: how much faster storage to set aside.
- **Replacement policy**: when the cache is full and new data comes in, **what gets thrown out?**

Next, a check on caching.
