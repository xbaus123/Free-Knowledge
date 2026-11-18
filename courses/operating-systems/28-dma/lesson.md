# Direct Memory Access

*Chapter 1 · Part 2: Computer-System Organization.*

Interrupt-driven I/O works well for a keyboard, which sends a byte now and then. But a fast SSD or a network card can deliver gigabytes a second. If the CPU took an interrupt and copied data **for every byte**, it would do nothing else.

## The fix: let the controller do the copying

**Direct memory access** (DMA) is used for **high-speed I/O devices** able to transmit information at close to memory speeds:

1. The OS sets up the transfer: it tells the device controller **where in memory** the data should go, and **how much** to move.
2. The device controller transfers **whole blocks of data from its buffer directly to main memory**, **without CPU intervention**.
3. When the whole block is done, the controller raises **one interrupt**.

Only **one interrupt is generated per block**, rather than one interrupt per byte. While the controller is copying, the CPU is free to do other work.

## How a modern computer works

```
 ┌──────────────────────┬─────┐  instruction execution cycle  ┌──────────────┐
 │  thread of execution │     │ ◄───────────────────────────► │ instructions │
 │                      │cache│  data movement                │   and data   │
 │       CPU (×N)       │     │ ◄───────────────────────────► │              │
 └──────────────────────┴─────┘                               │    memory    │
     │ I/O      ▲ data   ▲ interrupt                          └──────────────┘
     ▼ request  │        │                                          ▲
   ┌───────────────────────┐            DMA                         │
   │      device (×M)      │ ───────────────────────────────────────┘
   └───────────────────────┘
```

This is a **von Neumann architecture**: instructions and data share the same memory. The CPU runs the **instruction execution cycle**, fetching instructions and data from memory through its cache. It sends **I/O requests** to devices, and devices answer with **interrupts**. And with **DMA**, devices move data **straight to memory**, bypassing the CPU.

Next, a check on DMA.
