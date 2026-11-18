# Storage Structure

*Chapter 1 · Part 2: Computer-System Organization.*

A program has to be in memory to run. But memory is small, expensive, and forgets everything when the power goes off. So computers use several kinds of storage.

## Main memory

**Main memory** (RAM) is the **only large storage area the CPU can access directly**. Every instruction the CPU runs, and every piece of data it works on, has to be in main memory (or in registers).

- It's **random access**: any byte can be read as quickly as any other, in any order.
- It's typically **volatile**: its contents are **lost when the power is turned off**.

## Secondary storage

**Secondary storage** is an **extension of main memory** that provides **large, nonvolatile** storage capacity. Nonvolatile means it keeps its contents without power. Your programs and files live here until they're loaded into memory.

### Hard disks

A **hard disk drive** (HDD) has rigid metal or glass **platters** covered with magnetic recording material, spinning under read-write heads.

- Each surface is logically divided into circular **tracks**, which are subdivided into **sectors**.
- The **disk controller** determines the logical interaction between the device and the computer: it turns "read block 7" into moving the heads and waiting for the right sector to spin by.

Moving parts make HDDs slow: milliseconds per access, millions of times longer than a CPU instruction.

### Solid-state disks

**Solid-state disks** (SSDs) store data in **flash memory** chips, with no moving parts.

- **Faster than hard disks**, and **nonvolatile**.
- Built from various technologies, and **becoming more popular** every year. Most new laptops ship with SSDs only.

## Volatile vs nonvolatile

| | Main memory | Hard disk | SSD |
|---|---|---|---|
| CPU can access directly? | **Yes** | No | No |
| Survives power off? | No (volatile) | Yes | Yes |
| Moving parts? | No | Yes | No |
| Speed | Fastest of the three | Slowest | In between |

Next, a check on storage structure.
