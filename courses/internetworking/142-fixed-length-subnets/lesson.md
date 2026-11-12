# Equal-Size Subnets of a /24

*Chapter 5 · Subnetting in Practice.*

The simplest plan cuts a network into subnets that are **all the same size**. This is **fixed-length subnetting**: one mask everywhere.

## 10.1.1.0/24 cut into four /26s

Borrow 2 bits → /26, netmask **255.255.255.192**, block size **64**.

| Subnet | Network | Router (first host) | Hosts | Broadcast |
|---|---|---|---|---|
| A | 10.1.1.0/26 | 10.1.1.1 | .2 – .62 | 10.1.1.63 |
| B | 10.1.1.64/26 | 10.1.1.65 | .66 – .126 | 10.1.1.127 |
| C | 10.1.1.128/26 | 10.1.1.129 | .130 – .190 | 10.1.1.191 |
| D | 10.1.1.192/26 | 10.1.1.193 | .194 – .254 | 10.1.1.255 |

A router with four interfaces joins them, one address on each subnet:

```
 subnet A  10.1.1.0/26     hosts .2   .3   .4   ── .1   ─┐
 subnet B  10.1.1.64/26    hosts .66  .67  .68  ── .65  ─┤
                                                         ├─[ router ]
 subnet C  10.1.1.128/26   hosts .130 .131 .132 ── .129 ─┤
 subnet D  10.1.1.192/26   hosts .194 .195 .196 ── .193 ─┘
```

Check yourself with the pattern: each **broadcast is one less than the next network** (63/64, 127/128, 191/192), and the last broadcast is .255.

## Which subnet is a host on?

Find the block that contains it.

- 10.1.1.**100**: 64 ≤ 100 < 128 → subnet **B**, 10.1.1.64/26
- 10.1.1.**191**: that's subnet C's **broadcast**, not a host
- 10.1.1.**192**: that's subnet D's **network address**, not a host either

## The weakness

Every subnet gets **62 hosts**, needed or not. Suppose subnet D only links two routers together: 60 addresses wasted. Suppose subnet A has 80 laptops: it doesn't fit, and you'd have to move everyone to a /25, which only leaves room for two subnets.

Real networks have groups of different sizes. That's the problem the next reading solves.

Next, a check on equal-size subnets.
