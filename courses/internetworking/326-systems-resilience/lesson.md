# Systems Resilience

*Chapter 10 · Resilience.*

So far: hardware, firmware, software, one piece at a time. But nothing runs alone. A **system** is more than its parts.

## What is a system?

Donella Meadows, in *Thinking in Systems*, says a system has three things:

- **Elements**: the parts. Servers, routers, applications, **people**.
- **Interconnections**: how the parts relate. Network links, data flows, trust, who reports to whom.
- **Function** (or purpose): what the whole thing is for. Selling things online, running a hospital.

**Systems resilience** is the ability of a system to withstand, recover from, and adapt to adverse conditions: attacks, breaches, failures. Ideally the elements, functions, **and** interconnections are all resilient. In practice we spend most effort on the **elements** (patch the server!) and too little on the **interconnections** (what happens when a trusted link is abused?).

## How we do it today

| Area | Covers | Examples |
|---|---|---|
| **Technology** | Elements, functions | Anti-malware and anti-spam; firewalls and IDS/IPS; **segmentation**; SIEM and SOAR; encryption and VPNs; updates and patch management; redundancy |
| **Processes** | Functions, interconnections | Can we **isolate** a compromised system? Can we mobilize resources quickly? Where are backups stored? Is there a plan for each kind of event? |
| **People** | Elements, interconnections | Training and testing; alerting |

## The four Rs for a whole system

- **Robustness**: strong infrastructure, encryption, access control, and processes that run with **least privilege** and **fail closed**.
- **Resourcefulness**: **sharing threat intelligence** and coordinating with outside groups (vendors, industry groups, CERTs); **adaptive** security tools using machine learning; **prioritized** processes, by how they're used, by how important the asset is, or by other factors.
- **Redundancy**: hot and cold sites, multiple internet providers, backups.
- **Rapidity**: incident response, SIEM and SOAR, prioritized processes under least privilege for a quick recovery.

## What's still hard

- Making **functions** truly resilient: fault-tolerant systems and networks, deciding which failures matter most, keeping **partial** functionality during failures.
- Making **interconnections** truly resilient: **trust modeling** (who trusts whom, and should they?) and **traceability** (can you follow an action back to who did it?).
- **AI**: AI penetration-testing tools may help find weaknesses, and attackers will use AI too.
- **Insiders**: collusion and espionage by people with legitimate access are the hardest risks to detect, because they use real interconnections.

Next, a check.
