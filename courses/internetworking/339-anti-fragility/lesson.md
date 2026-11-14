# Anti-Fragility

*Chapter 10 · Resilience.*

Resilience means bouncing back to where you were. Can a system do better than that?

## Three kinds of systems

The writer Nassim Taleb sorts things into three groups:

| | Under stress | Example |
|---|---|---|
| **Fragile** | Breaks | A wine glass. A network with one firewall and no backups |
| **Resilient** (robust) | Survives, returns to how it was | A rubber ball. A network that fails over and recovers |
| **Anti-fragile** | Comes back **stronger** | Muscles after exercise. A network that learns from every incident |

**Anti-fragility** is the ability to **come back stronger**.

## How to make a network anti-fragile

- **Learn from every incident.** Hold a **post-incident review** (often called a blameless post-mortem): what happened, why, and what changes so it can't happen the same way again. Then actually make the changes.
- **Practice failure on purpose.** Tabletop exercises, restore drills, and **chaos engineering**: deliberately breaking things (turning off a server, cutting a link) in a controlled way to find weaknesses before an attacker or an accident does.
- **Feed what you learn back** into baselines, detection rules, training, and the incident response plan. Each attack becomes a test case.

## Is "hack back" anti-fragility?

**Hacking back** means attacking the attacker: breaking into the systems that attacked you. It can feel like coming back stronger, but it isn't:

- It doesn't make **your** systems any stronger.
- It's **illegal** for private organizations in most countries (in the US, under the Computer Fraud and Abuse Act).
- Attacks usually come **through** other victims' hijacked machines, so you'd hit an innocent hospital or home computer.
- It can **escalate** the conflict.

Anti-fragility is about **you** getting better, not about them getting hurt.

Next, a check.
