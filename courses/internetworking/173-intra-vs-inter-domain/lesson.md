# Intra-domain vs Inter-domain Routing

*Chapter 6 · Routing.*

The Internet is far too big for one routing protocol. No router could hold a link state map of the whole planet, and no company would hand its internal layout to its competitors. So routing is split in two.

## Autonomous systems

An **autonomous system (AS)** is a network, or group of networks, run by **one organization** with **one routing policy**: a university, a cloud provider, an ISP, a large company. Each has its own number, an **ASN**.

```
   ┌──── AS 64500 (a university) ────┐          ┌──── AS 64501 (its ISP) ────┐
   │  R1 ─ R2 ─ R3     (OSPF inside) │── BGP ───│   R7 ─ R8 ─ R9  (IS-IS)    │── BGP ── the rest
   │   └── R4 ──┘                    │          │                            │   of the Internet
   └─────────────────────────────────┘          └────────────────────────────┘
        intra-domain                inter-domain           intra-domain
```

## The two kinds

| | Intra-domain | Inter-domain |
|---|---|---|
| Also called | Interior gateway protocol (IGP) | Exterior gateway protocol (EGP) |
| Where | **Inside** one AS | **Between** ASes |
| Goal | Performance: the fastest path | Policy: who's allowed to carry whose traffic |
| What routers know | Every router in the domain. Anything outside is just the **default route** | Which ASes can reach which prefixes |
| Protocols | **RIP**, **OSPF**, IS-IS | **BGP** |
| Trust | One organization, so neighbors are trusted | Different organizations, so trust is the hard part |

Inside the AS, the operator can pick any protocol it likes, and can change it without telling anyone. Between ASes, everyone has to speak the same language: **BGP**.

## Why the split works

- **Scale.** Each AS hides its internal detail. The rest of the Internet only learns "AS 64500 has these prefixes."
- **Independence.** The university can switch from RIP to OSPF and no one outside notices.
- **Policy.** Business relationships between organizations get decided at the border, where they belong.

Next, a check on the two kinds of routing.
