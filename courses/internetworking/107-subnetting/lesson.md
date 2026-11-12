# Subnetting

*Chapter 4 · The Network Layer.*

**Subnetting** means borrowing bits from the host part to carve one network into smaller ones. You do it to match networks to real groups (one subnet per floor, department, or VLAN), to keep broadcasts contained, and to control what can talk to what at the routers between them.

## The block size shortcut

For any address and prefix, four answers matter: the **network address**, the **broadcast address**, the **usable range**, and the **number of hosts**. You can get them all without writing out binary, using the **block size**:

> **block size = 256 − the mask's interesting octet** (the one that isn't 255 or 0)

Subnets start at multiples of the block size.

**Example: 192.168.10.77/26.**

1. /26 is 255.255.255.**192**. The interesting octet is the 4th.
2. Block size = 256 − 192 = **64**. Subnets start at .0, .64, .128, .192.
3. 77 falls in the block starting at **64**.

| | |
|---|---|
| Network | 192.168.10.**64** |
| Broadcast | 192.168.10.**127** (one before the next block, 128) |
| Usable hosts | .65 to .126 |
| Count | 2⁶ − 2 = **62** |

## When the interesting octet is the 3rd

**Example: 10.104.216.118/22.** The mask is 255.255.**252**.0, so block size = 256 − 252 = **4**, in the 3rd octet: blocks start at 216, 220, 224... 216 is a multiple of 4, so:

- Network 10.104.**216.0**, broadcast 10.104.**219.255**
- Hosts 10.104.216.1 to 10.104.219.254: 2¹⁰ − 2 = **1,022**

## Splitting a network

To split one network into **n equal subnets**, borrow enough bits to count to n: 2 subnets need 1 bit, 4 need 2, 8 need 3.

192.168.1.0/24 split into **4** subnets: borrow 2 bits → **/26**, block size 64:

| Subnet | Hosts | Broadcast |
|---|---|---|
| 192.168.1.0/26 | .1 – .62 | .63 |
| 192.168.1.64/26 | .65 – .126 | .127 |
| 192.168.1.128/26 | .129 – .190 | .191 |
| 192.168.1.192/26 | .193 – .254 | .255 |

## Sizing for a number of hosts

Going the other way: find the fewest host bits **h** with **2ʰ − 2 ≥ hosts needed**, then the prefix is 32 − h.

- 50 hosts: 2⁶ − 2 = 62 ≥ 50, so h = 6 → **/26**
- 300 hosts: 2⁸ − 2 = 254 is too few; 2⁹ − 2 = 510 → **/23**
- A link between two routers needs 2 hosts: 2² − 2 = 2 → **/30**

Leave room to grow: a 50-person department that might double is better off with a /25.

Next, a check on subnetting.
