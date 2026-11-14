# Resilient Networks

*Chapter 10 · Resilience.*

Now the four Rs for the network itself: everything from chapters 2 to 8, built to survive.

## Robustness

- **Proper sizing**: links, switches, and firewalls with headroom for peaks and for attack traffic. A link running at 95% on a normal day has nothing left for a bad one.
- **Patch management**, and **staying current on releases** of router and switch software.
- **Network security products**: firewalls, VPNs, IDS and IPS.
- **Enforcing need to know**: **micro-segmentation** (small zones, even per server or per application, with rules between them) and **authentication** for devices and users. An attacker who gets into one zone shouldn't reach the rest.
- **Monitoring and logging**: you can't defend what you can't see.

## Redundancy

- **Load balancing** or **load sharing**:
  - **Load balancing** spreads requests across equal servers, using health checks to skip a dead one.
  - **Load sharing** splits traffic across several paths or links, not necessarily evenly. Two internet links might carry 70% and 30%.
  - Either way, losing one means less capacity, not an outage.
- **Hot and cold backups** of equipment and configurations. A saved switch configuration turns a 3-hour rebuild into a 10-minute restore.
- **Multiple providers**, over physically separate routes. Two "different" providers in the same trench are cut by the same backhoe.

## Resourcefulness

- **Prioritizing network services.** Some services everything else depends on:
  - **Routing**: nothing moves without it.
  - **Name service** (DNS, chapter 7): nothing can find anything without it.
  - **Logging**: without it you're blind during the incident.
  - **Notifications**: alerts and paging, so people know.

  These come back first.
- **Repurposing servers**: put infrastructure services (DNS, DHCP, logging) on **more than one** server, so any of them can take over the job.

## Rapidity

- **Reload versus restart**, when possible. A **reload** tells a service to reread its configuration while it keeps running, like `systemctl reload nginx`. A **restart** stops it and starts it again, dropping every connection. Reload is faster and gentler. (Careful with words: on a Cisco router, `reload` means reboot the whole device.)
- **Metrics**: **TTR** (time to recover or repair) and **availability**. Track them per service and per incident, and watch the trend.

## Putting it together

| R | Network measure |
|---|---|
| Robustness | Sizing, patches, firewalls and IDS, micro-segmentation, logging |
| Resourcefulness | Critical services first: routing, DNS, logging, notifications. Infrastructure services on several servers |
| Redundancy | Load balancing or sharing, backups of configs, multiple providers on separate paths |
| Rapidity | Reload instead of restart, TTR and availability tracked |

Next, a check.
