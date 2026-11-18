# The Storage Hierarchy

*Chapter 1 · Part 2: Computer-System Organization.*

Storage systems are organized in a **hierarchy**, ranked by three things that trade off against each other:

- **Speed**: how fast you can read or write it.
- **Cost**: price per byte.
- **Volatility**: whether it survives losing power.

## The pyramid

```
               registers            ▲ faster, smaller, more expensive per byte
               cache                │
             main memory            │
           solid-state disk         │
             hard disk              │
            optical disk            │
          magnetic tapes            ▼ slower, bigger, cheaper per byte
```

The higher a level, the **faster and more expensive** it is, and the **smaller**. The top levels (registers, cache, main memory) are volatile; from SSDs down, storage is nonvolatile.

## The numbers

| Level | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **Name** | Registers | Cache | Main memory | Solid-state disk | Magnetic disk |
| **Typical size** | < 1 KB | < 16 MB | < 64 GB | < 1 TB | < 10 TB |
| **Technology** | Custom memory with multiple ports (CMOS) | On-chip or off-chip CMOS SRAM | CMOS DRAM | Flash memory | Magnetic disk |
| **Access time (ns)** | 0.25–0.5 | 0.5–25 | 80–250 | 25,000–50,000 | 5,000,000 |
| **Bandwidth (MB/s)** | 20,000–100,000 | 5,000–10,000 | 1,000–5,000 | 500 | 20–150 |
| **Managed by** | Compiler | Hardware | Operating system | Operating system | Operating system |
| **Backed by** | Cache | Main memory | Disk | Disk | Disk or tape |

Look at the access times. A register takes under a nanosecond; a hard disk takes **5 million**. If a register read took one second, a disk read would take nearly two months.

## Who moves data between levels?

- **Registers** are managed by the **compiler**, which decides which variables live in them.
- **Cache** is managed by **hardware**, automatically.
- **Main memory and below** are managed by the **operating system**.

So movement between levels can be **explicit** (the OS deciding to copy a file block into memory) or **implicit** (the hardware quietly filling the cache).

Next, a check on the storage hierarchy.
