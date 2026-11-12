# Subnets and Zero Trust

*Chapter 5 · Subnetting in Practice.*

Every subnet in this chapter so far is a **physical subnet**: a range of addresses tied to real wires, switch ports, and VLANs. A laptop plugged into the staff jack lands on the staff subnet. That idea needs a second look under a modern security model.

## The old model: trust by location

Traditional networks work like a castle with a moat. The firewall at the edge keeps outsiders out, and **anything inside is trusted**. Subnets refine that a little: "anything on the server subnet may talk to the database". Either way, **where you are on the network decides what you're allowed to do**.

The weakness: once an attacker gets **one** foothold inside (a phished laptop, an unpatched camera), they inherit that location's trust and can move sideways to everything else on the subnet.

## Zero Trust

**Zero Trust Architecture (ZTA)**, described in NIST SP 800-207, starts from the opposite assumption: **no device or user is trusted because of its network location.** Being on the staff subnet proves nothing. Every request is checked on its own:

- **Who** is asking (the user's identity, with MFA)?
- **What** device are they using, and is it healthy (patched, managed)?
- Is **this** request, to **this** resource, allowed right now?

Access is granted per session, with the **least privilege** needed.

## So why do physical subnets still matter?

Because Zero Trust doesn't throw subnets away. It stops *trusting* them. Subnets still:

- **Contain broadcasts** and keep traffic volumes manageable.
- **Limit the blast radius**: an attacker on the camera subnet still has to get through a router or firewall to reach anything else.
- Carry **microsegmentation**: very small segments, sometimes one per workload, each with its own policy.

What changes is that an IP address or subnet becomes **one signal among many**, never the whole answer.

## Why VLSM can cause trouble in a ZTA

VLSM is efficient with addresses, but it can make Zero Trust policy harder:

- **Irregular boundaries.** Firewall rules written as address ranges get messy when subnets are /25, /28, and /30 side by side. A typo in a mask quietly includes or excludes the wrong hosts.
- **Resizing breaks rules.** When a /28 outgrows itself and becomes a /27, every policy that named the old range must be found and fixed. Miss one, and access is either broken or wider than intended.
- **Address ≠ identity.** VLSM packs many small groups into one block, which tempts people to write policies by subnet ("10.1.1.192/28 is the servers"). Zero Trust says the policy should name the **workload or user**, not the address it happens to have today.
- **Visibility.** Many tiny subnets mean more routes, more gateways, and more places for a gap in logging or monitoring.

The lesson isn't "don't use VLSM". It's: **plan subnets for traffic and organization, and build security on identity, with the subnet as a backstop.**

Next, a check on subnets and Zero Trust.
