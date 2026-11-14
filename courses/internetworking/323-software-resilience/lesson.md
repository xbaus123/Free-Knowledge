# Software Resilience

*Chapter 10 · Resilience.*

**Software resilience** is a software system's capacity to resist and recover from errors, disturbances, or attacks while keeping its core features and a decent user experience. It comes from redundancy and replication, error handling and fault tolerance, monitoring and alerting, and rapid recovery.

## Robustness

- **Backups with version control**: every change to code and configuration is tracked, so you can roll back to the last version that worked.
- **Disaster recovery** plans for each application.
- **Patch management**: knowing what's installed, and getting updates out on a schedule.
- **Software security testing tools** that scan code and running applications for weaknesses.
- **Integrity assurance**: hashes and code signing, so you can tell if a program has been changed.
- **Fail closed, restart with least privilege**:
  - When a security component fails, it should **fail closed**: deny access, rather than **fail open** and let everything through. A firewall that crashes should block traffic, not pass it.
  - When it restarts, it should run with the **least privilege** it needs, not as administrator.

Fail closed isn't always right. A door lock on a fire exit must **fail open**, or it traps people. Choose per component: safety or security.

## Resourcefulness

- **EDR**, endpoint detection and response: software on each computer that watches for attack behavior and can isolate the machine.
- **SOAR**, security orchestration, automation, and response: runs **playbooks** automatically, like "if this alert fires, disable the account and open a ticket."
- **Process workflows**, and **SLAs** (service level agreements) for software processes: what's promised, and how fast.
- **Knowing which components are critical**, and **prioritizing** them.

## Redundancy

- **Load balancing** across several copies of an application.
- **Failover** systems and services.
- **Cloud** service redundancy, across regions or providers.
- **QoS agreements**, so critical traffic keeps its share when links are busy.
- **Clustering.**

## Rapidity

- **SIEM**, security information and event management: collects logs from everywhere, **correlates** them, and alerts on patterns. SIEM spots the problem; SOAR acts on it.
- **Incident response** and **SLAs**.
- **Dependency modeling**: a map of what depends on what. If the authentication service is down, which applications break with it?
- **Weighted paths**: giving each dependency a weight (how critical it is, how long it takes to restore), so recovery follows the best order.

Next, a check.
