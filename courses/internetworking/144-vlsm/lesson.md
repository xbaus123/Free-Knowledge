# Variable Length Subnet Masks

*Chapter 5 · Subnetting in Practice.*

**VLSM (Variable Length Subnet Masks)** means using **different masks for different subnets** of the same network. It recognizes two facts of life:

- Some subnets are **busier** than others.
- Some subnets have far **fewer hosts** than others. A link between two routers has exactly 2.

So instead of one size for everyone, you give each subnet the smallest block that fits it.

## The method: biggest first

1. List the subnets you need, with host counts (plus growth).
2. For each, find the smallest prefix where **2ʰ − 2 ≥ hosts**. Use the cheat sheet.
3. Sort them **largest first**.
4. Hand out blocks from the bottom of the address space, in that order. Each block must start on a **multiple of its own size**.

Going largest first is what keeps step 4 working: a big block always lands on a boundary that suits it, and the small blocks fill in after.

## Example: one /24, five subnets

You have **10.1.1.0/24** and need:

| Need | Hosts | Smallest fit | Block size |
|---|---|---|---|
| Staff | 100 | /25 (126 hosts) | 128 |
| Lab | 50 | /26 (62 hosts) | 64 |
| Printers & servers | 12 | /28 (14 hosts) | 16 |
| Router link 1 | 2 | /30 (2 hosts) | 4 |
| Router link 2 | 2 | /30 (2 hosts) | 4 |

Allocate largest first:

| Subnet | Network | Broadcast | Usable | Mask |
|---|---|---|---|---|
| Staff | 10.1.1.0/25 | 10.1.1.127 | .1 – .126 | 255.255.255.128 |
| Lab | 10.1.1.128/26 | 10.1.1.191 | .129 – .190 | 255.255.255.192 |
| Printers & servers | 10.1.1.192/28 | 10.1.1.207 | .193 – .206 | 255.255.255.240 |
| Router link 1 | 10.1.1.208/30 | 10.1.1.211 | .209 – .210 | 255.255.255.252 |
| Router link 2 | 10.1.1.212/30 | 10.1.1.215 | .213 – .214 | 255.255.255.252 |
| *Free* | 10.1.1.216 – .255 | | 40 addresses left for later | |

With fixed-length /26s, this wouldn't fit at all: the 100-host staff subnet needs more than 62.

## Small pieces carved out of a block

You can also take one block and split it further. Here a /28 and a /30 are carved from the low end of 10.1.1.0/24, the way the lecture diagram does it:

```
 10.1.1.4/30    network .4   router .5   host .6   broadcast .7
 10.1.1.16/28   network .16  router .17  hosts .18 – .30   broadcast .31
```

The /30 starts at **4** (a multiple of 4) and the /28 starts at **16** (a multiple of 16). A /28 can't start at 8: 8 isn't a multiple of 16, so 10.1.1.8/28 isn't a real network (ANDing .8 with .240 gives .0).

## Rules for VLSM

- Subnets **must not overlap**. Check that each new block starts after the last one's broadcast.
- Every block starts on a **multiple of its size**.
- Your routing protocol must **carry masks** (RIPv2, OSPF, EIGRP). Classful RIPv1 can't do VLSM.

Next, a check on VLSM.
