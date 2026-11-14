# SDN Security

*Chapter 6 · Routing.*

SDN introduces new security challenges, and some of them probably haven't been found yet. Here's what's known.

## OpenFlow messages an attacker would love

The controller talks to switches on a TCP port that varies by vendor: **6653** is the official OpenFlow port, and **6633**, 6640, 443, 80, 8080, and 8043 all show up too. Anyone who can speak to a switch as its controller can send:

| Controller → switch | What it does |
|---|---|
| `OFPT_FLOW_MOD` | Add, delete, or modify the switch's **flow table** |
| `OFPT_PACKET_OUT` | Send a packet out a port; can **inject** packets into the data plane |
| `OFPT_PORT_MOD` | Reconfigure a switch port |
| `OFPT_TABLE_MOD` | Change how a table handles traffic types, like fragmented packets |
| `OFPT_GROUP_MOD` | Add, modify, or delete group entries |
| `OFPT_METER_MOD` | Add, modify, or delete meters (rate limits) |

| Switch → controller (async) | When it's sent |
|---|---|
| `OFPT_PACKET_IN` | A packet matched no rule: "what should I do?" |
| `OFPT_FLOW_REMOVED` | A flow entry was removed, usually after inactivity |
| `OFPT_PORT_STATUS` | A port went up or down |

`FLOW_MOD` alone is enough to redirect, copy, or black-hole any traffic on the switch.

## Threats and defenses

| Vulnerability | Defenses |
|---|---|
| Single point of failure | **Redundant** controllers; harden the controller |
| API vulnerabilities | Secure the northbound and southbound APIs; vet applications |
| Software and OS bugs | Regular updates and patching, code review, application vetting |
| Denial of service | Rate-limiting rules, segmentation |
| Man-in-the-middle | Network segmentation, endpoint security (and TLS on the controller channel) |
| Topology discovery attacks (fake links) | Segmentation, ACLs |
| Configuration attacks | Strong authentication and authorization (A&A), audits and reviews |
| Insider threats | Strong A&A, segmentation |
| `PACKET_IN` flooding | Patching, ACLs that drop invalid packets, monitoring |
| No system integrity checking | Harden the system: remove unused services, harden the kernel, least privilege |

**PACKET_IN flooding** deserves a closer look. Every packet that matches no rule gets sent up to the controller. An attacker who sends a flood of packets with **random, never-seen headers** makes every switch ask the controller about every one, and the controller drowns.

Next, a check on SDN security.
