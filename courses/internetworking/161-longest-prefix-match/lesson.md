# Longest Prefix Matching

*Chapter 6 · Routing.*

A forwarding table doesn't list every address. It lists **prefixes**, and a destination can match several of them at once. The rule:

> Use the **longest** prefix in the table that matches the destination address.

You met this idea when CIDR was introduced. Here's how a router applies it.

## An example table

| Destination prefix | In binary (prefix bits only) | Interface |
|---|---|---|
| 200.23.16.0/21 | 11001000 00010111 00010 | 0 |
| 200.23.24.0/24 | 11001000 00010111 00011000 | 1 |
| 200.23.24.0/21 | 11001000 00010111 00011 | 2 |
| otherwise (0.0.0.0/0) | (no bits) | 3 |

**Destination 200.23.22.161** = 11001000 00010111 **00010**110 10100001
- Matches the first row's 21 bits. Doesn't match rows 2 or 3. → **interface 0**.

**Destination 200.23.24.170** = 11001000 00010111 **00011000** 10101010
- Matches row 2 (24 bits) **and** row 3 (21 bits). The /24 is longer, so it wins → **interface 1**.

**Destination 10.0.0.1** matches only the default route → **interface 3**.

## Why longest wins

A longer prefix is a **more specific** route. The /21 says "this whole block is over there," while the /24 says "except this part, which is over here." Longest match lets one specific exception sit inside a big summary route, which is exactly what CIDR aggregation needs. The default route, at /0, is the least specific of all, so it only wins when nothing else matches.

## How routers do it fast: TCAM

A big router's table has around a million prefixes, and it has to look one up for every packet at line rate. Searching a list would be far too slow. Routers use **ternary content-addressable memory (TCAM)**:

- **Content-addressable**: you give it the address, and it returns the matching entry. All entries are compared **at once**, in parallel.
- **Ternary**: each bit can be 0, 1, or **"don't care"** (the `*` bits after the prefix).
- Entries are stored longest first, so the first match is the longest match.
- A lookup takes **one clock cycle**, no matter how big the table is.

The price: TCAM is expensive and power-hungry, which is one reason routers care about keeping tables small.

Next, a check on longest prefix matching.
