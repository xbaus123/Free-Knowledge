# Laying Out Your Subnets

*Chapter 5 · Subnetting in Practice.*

You know *why* to subnet. Next: **what goes in each subnet?** There are three common ways to slice an organization, and most real networks mix them.

## By function

One subnet per **kind of device or role**: staff laptops, servers, printers, VoIP phones, cameras, guests.

- **Good for security**: devices with the same job need the same rules, so the firewall rules are simple. *Cameras talk only to the video recorder.*
- **Good for quality of service**: put the phones on their own subnet and it's easy to prioritize voice.
- **Watch out**: one function may span several buildings, so a subnet (and its VLAN) has to stretch across them.

## By location

One subnet per **building, floor, or site**: 10.**1**.x.x for headquarters, 10.**2**.x.x for the warehouse.

- **Good for troubleshooting**: an address tells you where to walk.
- **Good for routing**: each site's router advertises one summary (10.2.0.0/16) instead of dozens of small routes.
- **Watch out**: everybody on a floor shares a subnet, the intern and the payroll server alike, so it doesn't help much with security on its own.

## By project

One subnet per **team or project**: the 2026 lab build, the research group, the merger team.

- **Good for isolation**: a project's machines can be walled off and handed its own budget of addresses.
- **Good for cleanup**: when the project ends, the whole subnet is reclaimed at once.
- **Watch out**: projects come and go, so the plan changes more often.

## Other ways, and mixing them

You might also slice by **security level** (public-facing, internal, restricted) or by **department**. In practice most networks combine two: location in one octet and function in the next.

```
 10 . site . function . host
 10 .  1   .    10    . 37     headquarters, staff, host 37
 10 .  2   .    40    . 5      warehouse, cameras, host 5
```

Whatever you pick, write it down. A layout only helps if everyone follows the same pattern.

Next, a check on laying out subnets.
