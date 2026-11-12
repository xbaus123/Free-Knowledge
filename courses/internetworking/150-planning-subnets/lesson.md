# Project: Subnet Your Network

*Chapter 5 · Subnetting in Practice.*

In chapter 4 you gave your project network its addresses. This time, **subnet your internal network**.

- You may create **more than one subnet**, and most designs should.
- **Bonus:** fit the whole design inside a single **class C** (/24). A /24 only has 256 addresses, so it forces you to size every subnet carefully with VLSM.

## Step by step

1. **List the groups** from your layout (function, location, project, or a mix).
2. **Count devices** in each, then add growth. Don't forget the router, printers, access points, and switch management addresses.
3. **Pick a prefix** for each with the cheat sheet: the smallest where 2ʰ − 2 covers the count.
4. **Allocate largest first**, each block on a multiple of its size.
5. For each subnet, write down the **network, mask, gateway (first usable), broadcast, and which part is static vs DHCP**.
6. **Check**: no overlaps, everything inside your block, room left over.

## A worked example: the office in one class C

The chapter 4 office again, but this time squeezed into **192.168.10.0/24**:

| Group | Devices with growth | Prefix | Block |
|---|---|---|---|
| Staff | 100 | /25 (126) | 128 |
| Guests | 50 | /26 (62) | 64 |
| Cameras | 20 | /27 (30) | 32 |
| Servers & printers | 10 | /28 (14) | 16 |
| Firewall-to-router link | 2 | /30 (2) | 4 |

Total: 128 + 64 + 32 + 16 + 4 = **244** of 256 addresses. It fits.

| Subnet | Network | Gateway | Broadcast | Addressing |
|---|---|---|---|---|
| Staff | 192.168.10.0/25 | .1 | .127 | .2–.20 static, .21–.126 DHCP (8-hour lease) |
| Guests | 192.168.10.128/26 | .129 | .191 | DHCP only, 1-hour lease, internet only |
| Cameras | 192.168.10.192/27 | .193 | .223 | Static, no internet |
| Servers & printers | 192.168.10.224/28 | .225 | .239 | Static |
| Link | 192.168.10.240/30 | .241 / .242 | .243 | Static |
| *Free* | 192.168.10.244 – .255 | | | 12 addresses spare |

Things to notice:

- Every gateway is the **first usable** address.
- The guest subnet is **all DHCP with a short lease**, so departed phones don't hog the pool.
- Static and dynamic ranges **never overlap**.
- The plan is tight: if staff grows past 126, something has to move. That's the price of the class C bonus. Write down what you'd do (for example, move to a /23, or move guests elsewhere).

## Questions your write-up should answer

- Which layout did you choose (function, location, project), and why?
- How many hosts does each subnet hold, and how much room is left?
- Which devices are static, and where in each subnet do they live?
- What lease time does each DHCP pool use?
- How would the plan change under Zero Trust: what would you still control by subnet, and what by identity?

Next, a check on planning your subnets.
