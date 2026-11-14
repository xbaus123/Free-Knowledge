# Redundancy and Rapidity

*Chapter 10 · Resilience.*

The other two Rs take over once something has actually broken: a **spare** to keep going, and a **plan** to get back fast.

## Redundancy

**Definition:** the ability to use **parallel** resources, systems, and data to keep functioning during an incident.

**Implementation:**

- **Backup systems**, hot and cold (more on these in the hardware lesson).
- **Fault tolerance** and **failover**: when one unit dies, another takes over automatically.
- **Clustering**: several servers acting as one.
- **Cloud** resources in more than one region.
- **Parallel processing** and **load balancing or load sharing**: spread the work, so losing one worker just slows things down.
- **Resource management software** to track it all.

**Metrics:**

- **Uptime.**
- **Functionality**: did data stay intact, and did critical functions keep working?
- **Loss metrics**: data lost, transactions lost, money lost.
- **Unreadiness**: how long a spare was *not* ready when you needed it.

A spare you haven't tested isn't really a spare. A failover that has never been triggered might not work on the one day it matters.

## Rapidity

**Definition:** the ability to quickly **identify, respond to, and recover** from an incident, back to a full functional state.

**Implementation:**

- An **incident response plan**: who does what, who calls whom, written down **before** the incident.
- **Real-time monitoring**, so you find out in minutes, not when a customer complains.

**Metrics:**

- **Recovery time**, often split into time to **detect**, to **respond**, and to **recover**. You'll see **TTR** (time to recover or repair) in the network lesson.
- **Functionality** restored, and how much.
- **Reconstitution** of applications and resources: rebuilt, reloaded, and verified.

Two targets many organizations set in advance:

| Target | Question | Example |
|---|---|---|
| **RTO**, recovery time objective | How long can we be down? | The shop must be back within 4 hours |
| **RPO**, recovery point objective | How much data can we lose? | At most 1 hour of orders, so back up at least hourly |

## The four Rs together

| R | Before | During | After |
|---|---|---|---|
| Robustness | Patch, train | Absorb the hit | |
| Resourcefulness | Plan priorities | Move people and money to what matters | |
| Redundancy | Build spares | Fail over | |
| Rapidity | Write the plan, set up monitoring | Detect fast | Recover fast |

Next, a check.
