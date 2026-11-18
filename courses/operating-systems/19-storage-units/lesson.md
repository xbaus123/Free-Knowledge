# Bits, Bytes, and Words

*Chapter 1 · Part 2: Computer-System Organization.*

Before we look at where data is stored, let's pin down how we measure it. You'll use these units in every chapter that follows.

## The basic units

- A **bit** holds one of two values: **0 or 1**. Everything a computer stores (numbers, letters, images, music, programs) is built from collections of bits.
- A **byte** is **8 bits**. On most computers it's the smallest convenient chunk of storage: there's usually no instruction to move a single bit, but there is one to move a byte.
- A **word** is a given architecture's **native unit of data**, made of one or more bytes. A computer with **64-bit registers and 64-bit addressing** typically has **64-bit (8-byte) words**, and does most of its operations a word at a time.

## Bigger units

Storage is measured in bytes and powers of 1,024 (that's 2¹⁰):

| Unit | Bytes | Power of two |
|---|---|---|
| **Kilobyte (KB)** | 1,024 | 2¹⁰ |
| **Megabyte (MB)** | 1,024² = 1,048,576 | 2²⁰ |
| **Gigabyte (GB)** | 1,024³ | 2³⁰ |
| **Terabyte (TB)** | 1,024⁴ | 2⁴⁰ |
| **Petabyte (PB)** | 1,024⁵ | 2⁵⁰ |

## Two catches

**Manufacturers round.** Disk makers often say a megabyte is 1 million bytes and a gigabyte is 1 billion. That's why a "1 TB" drive shows up as about 931 GB in your OS: 10¹² ÷ 1,024³ ≈ 931.

**Networks count bits.** Network speeds are given in **bits** per second, because networks move data one bit at a time. A 100 Mbps link moves 100 million *bits* a second, which is only 12.5 million *bytes*. Watch for the lowercase **b** (bits) versus uppercase **B** (bytes).

Next, a check on storage units.
