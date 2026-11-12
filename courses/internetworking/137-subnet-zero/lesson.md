# The Lowest and Highest Subnets

*Chapter 5 · Subnetting in Practice.*

An old subnetting rule says: **don't use the lowest subnet, and don't use the highest one.** You'll still meet it on exams and in older documentation, so it's worth knowing why it existed and why it's mostly gone.

## The two troublemakers

Split 192.168.1.0/24 into four /26s:

| Subnet | Range | Nickname |
|---|---|---|
| 192.168.1.**0**/26 | .0 – .63 | **subnet zero** (subnet bits all 0s) |
| 192.168.1.64/26 | .64 – .127 | |
| 192.168.1.128/26 | .128 – .191 | |
| 192.168.1.**192**/26 | .192 – .255 | **all-ones subnet** (subnet bits all 1s) |

## Why not the lowest?

Look at subnet zero's network address: **192.168.1.0**. That's *exactly* the network address of the whole /24. Written without a mask, "192.168.1.0" could mean either one.

Old **classful** routing protocols, like RIP version 1, didn't send masks with their routes. A router hearing "192.168.1.0" had no way to tell the big network from its first subnet.

## Why not the highest?

The all-ones subnet's broadcast address is **192.168.1.255**. That's *exactly* the broadcast address for the whole /24. A packet sent there could mean "every host on the last subnet" or "every host on every subnet". Same ambiguity, other end.

## The cost of the rule

Skipping both throws away two subnets:

- Usable subnets = **2ⁿ − 2** instead of 2ⁿ
- Borrowing 2 bits gives **2** usable /26s instead of 4. Borrowing 1 bit gives **zero**, so /25s were useless under the old rule.

That's why older examples say things like "subnet a /8 into /16s: 23.**n**.0.0 where n = 1 to 254". The 23.0.0.0/16 and 23.255.0.0/16 subnets are skipped.

## Today

Modern routing protocols (RIPv2, OSPF, EIGRP, BGP) **carry the mask with every route**, so there's no ambiguity, and RFC 1878 (1995) says subnet zero and the all-ones subnet are fine to use. Cisco routers have allowed subnet zero by default since the late 1990s.

> **Rule of thumb:** use all 2ⁿ subnets on a modern network. If an exam or an older device says otherwise, subtract 2.

Notice this is a rule about **subnets**, not hosts. The first and last **addresses** inside each subnet (the network and broadcast addresses) are still never given to hosts. That's why hosts are always 2ʰ − 2.

Next, a check on subnet zero and the all-ones subnet.
