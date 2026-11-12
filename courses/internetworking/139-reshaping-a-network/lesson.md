# Reshaping a Big Network

*Chapter 5 · Subnetting in Practice.*

Time for worked examples. The approach is always the same: **find the mask, then the block size, then the network and broadcast addresses.**

## A class A made to look like class Bs

A large carrier holds the class A network **23.0.0.0/8**.

**As one /8:**

- Netmask: **255.0.0.0**
- Network: 23.0.0.0, broadcast: **23.255.255.255**
- One enormous broadcast domain of 16,777,214 hosts. Nobody runs a network like that.

**Subnetted into /16s**, so each piece is the size of a class B: borrow the whole 2nd octet (8 bits).

- Netmask: **255.255.0.0**
- Subnets: 23.**n**.0.0/16, 2⁸ = **256** of them
- Broadcast of each: 23.**n**.255.255. For example, 23.40.0.0/16 broadcasts to 23.40.255.255.
- Under the old "skip the lowest and highest" rule, n runs from **1 to 254**.

**Subnetted into /24s**, the size of a class C: borrow the 2nd and 3rd octets (16 bits).

- Netmask: **255.255.255.0**
- Subnets: 23.**n**.**n**.0/24, 2¹⁶ = **65,536** of them
- Broadcast of each: 23.n.n.**255**. For example, 23.40.7.0/24 broadcasts to 23.40.7.255.

When the prefix lands on an octet boundary, it's easy: the network octets stay, the host octets are 0 for the network and 255 for the broadcast.

## Mid-octet: a /28 in a class B

A company holds the class B **166.23.0.0/16** and has a host at **166.23.9.18/28**.

1. /28 → netmask **255.255.255.240**. The interesting octet is the 4th.
2. Block size: 256 − 240 = **16**. Blocks start at 0, 16, 32, 48...
3. 18 falls in the block starting at **16**.

| | |
|---|---|
| Network | 166.23.9.**16**/28 |
| Broadcast | 166.23.9.**31** (one before the next block, 32) |
| Usable range | 166.23.9.**17** – 166.23.9.**30** (the router would be .17) |
| Usable hosts | 2⁴ − 2 = **14** |

## Mid-octet in the 3rd octet: a /20

The same company's other class B, **166.21.0.0/16**, has a subnet **166.21.16.0/20**.

1. /20 → netmask **255.255.240.0**. The interesting octet is the **3rd**.
2. Block size: 256 − 240 = **16**, counted in the 3rd octet: 0, 16, 32...
3. This subnet starts at **16** and the next starts at 32.

| | |
|---|---|
| Network | 166.21.**16.0**/20 |
| Broadcast | 166.21.**31.255** |
| Usable range | 166.21.16.**1** – 166.21.31.**254** |
| Usable hosts | 2¹² − 2 = **4,094** |

The broadcast ends in **31.255**, not 16.255: every bit after the prefix is a host bit, and that includes the low 4 bits of the 3rd octet *and* the whole 4th octet.

Next, a check on these examples.
