# Structure: Starting Simple with MS-DOS

*Chapter 2 · Part 7: Operating-System Structure.*

A general-purpose OS is a **very large program**. How do you organize millions of lines of code so it can be understood, changed, and trusted? There are several ways to structure one:

| Structure | Example |
|---|---|
| **Simple structure** | MS-DOS |
| **More complex** (monolithic) | UNIX |
| **Layered** | An abstraction, used in teaching and in parts of real systems |
| **Microkernel** | Mach |

Plus two modern approaches built from those: **loadable modules** and **hybrids**. This part takes them one at a time.

## Simple structure: MS-DOS

MS-DOS was **written to provide the most functionality in the least space**. It ran on 1980s PCs with very little memory, so compactness won over everything else.

- It's **not divided into modules**.
- It has *some* structure, but its **interfaces and levels of functionality are not well separated**.

```
   +-------------------------------+
   |     application program       |-------------+
   +-------------------------------+             |
        |                                        |
   +--------------------------+                  |
   |  resident system program |-------+          |
   +--------------------------+       |          |
        |                             |          |
   +------------------------+         |          |
   |  MS-DOS device drivers |         |          |
   +------------------------+         |          |
        |                             v          v
   +-----------------------------------------------+
   |            ROM BIOS device drivers            |
   +-----------------------------------------------+
```

Look at the arrows on the right: an **application program can skip every layer and call the BIOS device drivers directly**. Applications could write straight to the display or the disk.

## Why that's a problem

With nothing separating the levels, **a buggy or malicious program could crash the whole system**, or wipe the disk. MS-DOS couldn't have prevented it anyway: the Intel 8088 it ran on had **no dual mode and no hardware protection**, so there was no way to stop a program from touching the hardware.

A check on structure basics and MS-DOS.
