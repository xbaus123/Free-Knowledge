# The CIDR Cheat Sheet

*Chapter 5 · Subnetting in Practice.*

There are formulas for subnetting, and you learned them in chapter 4. But working network engineers mostly **look it up**: a printed CIDR cheat sheet, or an online subnet calculator. The trick is knowing how to read the table and spot its patterns, so you can rebuild any row in your head.

## The table

| Prefix | Former class C networks | Total addresses | Usable hosts | Netmask | Subnets of its class |
|---|---|---|---|---|---|
| /30 | 1/64 | 4 | 2 | 255.255.255.252 | 64 |
| /29 | 1/32 | 8 | 6 | 255.255.255.248 | 32 |
| /28 | 1/16 | 16 | 14 | 255.255.255.240 | 16 |
| /27 | 1/8 | 32 | 30 | 255.255.255.224 | 8 |
| /26 | 1/4 | 64 | 62 | 255.255.255.192 | 4 |
| /25 | 1/2 | 128 | 126 | 255.255.255.128 | 2 |
| /24 | 1 | 256 | 254 | 255.255.255.0 | 1 |
| /23 | 2 | 512 | 510 | 255.255.254.0 | 128 |
| /22 | 4 | 1,024 | 1,022 | 255.255.252.0 | 64 |
| /21 | 8 | 2,048 | 2,046 | 255.255.248.0 | 32 |
| /20 | 16 | 4,096 | 4,094 | 255.255.240.0 | 16 |
| /19 | 32 | 8,192 | 8,190 | 255.255.224.0 | 8 |
| /18 | 64 | 16,384 | 16,382 | 255.255.192.0 | 4 |
| /17 | 128 | 32,768 | 32,766 | 255.255.128.0 | 2 |
| /16 | 256 = 1 class B | 65,536 | 65,534 | 255.255.0.0 | 1 |
| /12 | 4,096 = 16 class Bs | 1,048,576 | 1,048,574 | 255.240.0.0 | 16 |
| /8 | 65,536 = 1 class A | 16,777,216 | 16,777,214 | 255.0.0.0 | 1 |

(The full sheet has every prefix from /8 to /31. The rows from /9 to /15 follow the same pattern as /17 to /23, one octet to the left.)

## How to read a row

Take **/27**:

- **Former class C networks: 1/8.** A /27 is an eighth of a /24.
- **Total addresses: 32**, of which **30 usable**: take away the network and broadcast addresses.
- **Netmask: 255.255.255.224.** Block size 256 − 224 = 32, which matches the total.
- **Subnets: 8.** A class C cut into /27s gives 8 of them.

The last column counts subnets **within the class that prefix falls in**. /27 is longer than /24, so it counts /27s in a class C (8). /20 is between /16 and /24, so it counts /20s in a class B (16).

## The patterns

1. **One step longer halves everything.** /26 → /27: addresses 64 → 32, and the number of subnets doubles.
2. **Usable = total − 2.** Always, except the /31 and /32 special cases.
3. **The netmask octets repeat**: 128, 192, 224, 240, 248, 252, 254, 255, in every octet.
4. **The subnet count resets at each class boundary**: /17 is 2 (of a B), /23 is 128 (of a B), /24 is 1 (of a C), /25 is 2 (of a C).

## Cheat sheet or formula?

Both give the same answers:

- Subnets from borrowing **n** bits: **2ⁿ**
- Usable hosts with **h** host bits: **2ʰ − 2**

The sheet is faster and harder to get wrong under pressure; the formula works when the sheet isn't in front of you. Online subnet calculators do the same thing for any address, but you're offline here, so this table is your calculator.

Next, a check on reading the cheat sheet.
