# Robustness and Resourcefulness

*Chapter 10 · Resilience.*

Each R has three parts: a **definition**, an **implementation** (what you actually do), and **metrics** (how you know it's working). This lesson covers the two Rs that matter most **before and during** an incident.

## Robustness

**Definition:** the ability to maintain **full or partial** functionality while under attack.

**Implementation:** mostly good hygiene, done consistently.

- **Patching** and keeping software updated, so known holes are closed.
- Up-to-date **security practices**: current configurations, strong authentication, sensible firewall rules.
- **User awareness**: training people to spot phishing, and alerting them when an attack is going around.

**Metrics:**

- **Readiness time**: uptime, or a "readiness" value for how often the system was ready to do its job.
- **Attacks detected and prevented.** Useful, but **fuzzy**: you can count the attacks you stopped, but not the ones you never noticed. Zero detected attacks might mean great defenses, or blind sensors.

## Resourcefulness

**Definition:** the ability to **prioritize, mobilize, and apply** resources during an incident.

During an incident you never have enough people, money, or machines to do everything. Resourcefulness is knowing **what to save first** and being able to move people and equipment there fast.

**Implementation:**

- **Training personnel**, so more than one person knows how to restore the database.
- **External expertise**: an incident response firm on retainer, or a vendor's support line.
- Proper **allocation of budget** to the resources that protect critical functions.
- **Resource management software** that shows what you have and where it's used.

**Metrics:**

- **Prioritized functionality**: is there an agreed list of what comes back first?
- **Readiness rankings**: tracking how ready each team and system is.
- **Multi-purpose people and technology**: a server that can take over another's job, a staff member trained in two roles.

## The two side by side

| | Robustness | Resourcefulness |
|---|---|---|
| Question | How much can we take? | What do we save first? |
| Mostly about | The systems | The people, money, and plans |
| Example | A patched server shrugs off a known exploit | When the mail server is down, staff move to the chat system and the IT lead works on payments first |

Next, a check.
