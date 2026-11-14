# Securing Routing Inside the Domain

*Chapter 6 · Routing.*

Inside one AS there's one owner, so routers trust each other more. That makes security **simpler, but weaker**: if an attacker gets onto the network and starts speaking OSPF, the routers may believe them. Here's how you defend an IGP like OSPF or IS-IS.

## Defenses, from the first line in

| Defense | What it does |
|---|---|
| **ACLs** | Still the **first line of defense**. Only accept routing traffic from known router addresses, on known interfaces |
| **Passive interfaces** | Don't send or accept routing hellos on ports that face users. No router should ever be on the guest Wi-Fi |
| **Authentication** | Neighbors share a secret key (symmetric) and sign every routing message. **MD5** is the old option; **HMAC-SHA** is the stronger one. A forged LSA without the key is ignored |
| **Rate limiting** | Cap how much routing traffic reaches the router's CPU, so a flood can't knock out the control plane. Excess is **dropped**, or **permitted at low priority** |
| **Prefix filtering** | Limit what each router may advertise. An access router should never announce the default route |
| **Control summarization** | Decide exactly which summaries cross area boundaries, so a mistake in one area doesn't spread |
| **Segmentation and design** | Separate the routing infrastructure from user networks, like the VLANs and subnets of chapters 3 to 5 |

## Stopping spoofed sources: ingress filtering

**Ingress filtering** drops packets arriving with a **source address that couldn't have come from there**. If the staff subnet is 10.1.10.0/24, a packet arriving from that subnet with source 8.8.8.8 is forged, so drop it. Done at the edge of every network, this stops a lot of spoofed-source attacks (best practice BCP 38). The IETF's **SAVNET** working group (source address validation) is extending the idea both inside and between domains.

## Keep a trail

Document what's configured and why, and **log** routing changes: neighbors coming up and down, routes added and withdrawn. When a route goes wrong, the audit trail is how you find out whether it was a typo or an attacker.

Next, a check on intra-domain routing security.
