# The Layered Approach

*Chapter 2 · Part 7: Operating-System Structure.*

What if you broke the kernel into neat rings?

## Layers

In the **layered approach**, the OS is **divided into a number of layers (levels), each built on top of lower layers**.

- The **bottom layer (layer 0) is the hardware**.
- The **highest (layer N) is the user interface**.

```
              +---------------------------+
              |  layer N: user interface  |
              |   +-------------------+   |
              |   |       ...         |   |
              |   |   +-----------+   |   |
              |   |   |  layer 1  |   |   |
              |   |   | +-------+ |   |   |
              |   |   | |layer 0| |   |   |
              |   |   | |  hw   | |   |   |
              |   |   | +-------+ |   |   |
              |   |   +-----------+   |   |
              |   +-------------------+   |
              +---------------------------+
```

**With modularity, layers are selected so that each uses functions (operations) and services of only lower-level layers.** Layer 3 may call layer 2 or layer 1, but never layer 4.

## Why it's attractive

- **Simple to build and debug.** Debug layer 1 first, using only the hardware. Once it works, debug layer 2, knowing that any bug must be in layer 2, because layer 1 is already correct. And so on up.
- **Each layer hides its details.** A layer only needs to know *what* the layers below do, not *how*.

## Why it's rare in pure form

- **Defining the layers is hard.** Everything must be strictly above what it uses. But the memory manager might need the disk driver (to swap pages to disk), and the disk driver might need memory management (for buffers). Who goes on top?
- **It's slow.** A request from the top has to pass down through every layer, and each crossing adds overhead.

So real systems use **a few layers with lots of functionality each**, getting some of the benefit without as much of the cost. The layered idea also shows up everywhere outside kernels: the network stack (TCP over IP over Ethernet) is the best-known example.

A check on layering.
