# Why We Subnet

*Chapter 5 · Subnetting in Practice.*

Chapter 4 gave you the arithmetic: masks, prefixes, block sizes, network and broadcast addresses. This chapter is about **using** it: why you'd cut a network up, the rules people follow when they do, and how to plan subnets of different sizes for a real organization.

## A subnet is a network

First, a point that trips people up: **a subnet is a network**. It has its own network address, its own broadcast address, and its own range of hosts. "Subnet" only says it was carved out of something bigger. To a router, 10.1.1.0/26 is just another network to forward to.

So when you subnet, you're **creating more networks**, and the hosts on different subnets talk to each other **through a router**.

## Three reasons to subnet

**1. Manageable traffic volume.**
Every subnet is its own **broadcast domain**. ARP requests, DHCP discovers, and other broadcasts reach every host on the subnet, and on a flat network of 5,000 hosts that chatter adds up. Cut it into twenty subnets of 250 and each broadcast reaches 250 hosts, not 5,000.

**2. Keep things organized.**
If the third octet tells you the floor or the department, you can read an address and know where it lives. 10.1.**20**.37 is on floor 2; a problem with 10.1.20.0/24 is a problem on floor 2. Troubleshooting, documentation, and growth are all easier.

**3. Security.**
Traffic between subnets has to pass through a router, and a router (or firewall) can **filter** it. Put the guest WiFi, the cameras, and the payroll servers on separate subnets and you can write rules like *guests may reach the internet but nothing internal*. On one flat network there's no place to put that rule.

```
 Flat: one /22, 1,022 hosts
   [ staff  guests  cameras  servers ]   every host hears every broadcast,
                                         and nothing sits between them

 Subnetted: four /24s
   [ staff ]──┐
   [ guests]──┤
              ├──[ router / firewall ]   broadcasts stay in each subnet,
   [cameras]──┤                          and the router can filter
   [servers]──┘
```

Next, a quick check on why we subnet.
