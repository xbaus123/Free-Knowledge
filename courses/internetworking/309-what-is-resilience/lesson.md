# What Is Resilience?

*Chapter 10 · Resilience.*

Chapters 1 to 9 built a network from the cables up and put a website on top of it. This chapter asks a different question: **what happens when something goes wrong?** A disk dies, a vendor gets hacked, a router is misconfigured, an attacker gets in. A network that keeps working, or comes back fast, is **resilient**.

## More than "it stays up"

It's tempting to say resilience just means **availability**: the system is up. But a system can be up and still useless. The web server answers, but the database behind it has been quietly corrupted. Or it's up only because it has never been tested by a real incident.

Resilience is the ability to **keep critical functions working during an incident, and to get back to full function afterwards**. It covers the whole incident: before, during, and after.

## The four Rs

There are many definitions. This course uses one from Bishop, Carvalho, and colleagues, which borrows the **four Rs** from disaster engineering (Tierney and Bruneau used them for earthquakes and bridges):

| R | The question it asks | In one line |
|---|---|---|
| **Robustness** | How much can we take? | Keep working, fully or partly, while under attack |
| **Resourcefulness** | Can we focus what we have? | Prioritize resources so critical functions keep working |
| **Redundancy** | Is there a spare? | Replace failing functions on the fly |
| **Rapidity** | How fast do we bounce back? | Return to full function quickly |

The four work together. Robustness limits **how far** you fall. Redundancy and resourcefulness keep the **critical** parts going while you're down. Rapidity decides **how long** you stay down.

## The resilience triangle

Draw a graph: **functionality** (0 to 100%) up the side, **time** along the bottom. An incident knocks functionality down, and recovery brings it back up. The dip forms a triangle, and its **area** is what the incident cost you.

- A more **robust** system has a shallower dip.
- A more **rapid** one recovers sooner, so the triangle is narrower.

Recovery doesn't have to be all or nothing, either. Getting the shop's checkout back at 50% capacity is a degree of restoration, and worth measuring.

## Tying metrics to the business

"99.9% uptime" means little to a manager. "Each hour the shop is down costs about $4,000 in lost orders" means a lot. A good resilience metric can be turned into **business impact**: lost sales per hour, orders delayed, customers affected, fines for a missed deadline. Then a $2,000 spare server becomes an easy decision.

Next, a check on the four Rs.
