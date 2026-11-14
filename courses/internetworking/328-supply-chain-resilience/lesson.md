# Supply Chain Resilience

*Chapter 10 · Resilience.*

Your network is built from things other people made: hardware, firmware, software, cloud services, even the trucks that deliver spare parts. Every one of those suppliers is a possible way in. A **supply chain attack** goes after a supplier to reach its customers.

The best-known example: in **2020**, attackers broke into **SolarWinds** and slipped a backdoor into an update of its Orion network-monitoring software. Thousands of organizations, including US government agencies, installed the signed, official update. The customers did nothing wrong; their supplier was compromised.

## Questions to ask

- What **safeguards** are built in at each point where the supply chain could be attacked?
- What **prevention and detection** covers those points?
- What **proactive** measures are there, beyond reacting?
- How is resilience planned for **new and evolving** attacks?
- If a **third-party vendor is compromised**, how would you **detect** it, and how would you **contain** it so it doesn't spread further down the chain?

## The four Rs

**Robustness**

- **Multiple suppliers** for critical components.
- **Encryption**, **access control**, and **authentication** on every link with a supplier: vendors get the access they need and no more.
- **Cyber insurance requirements**: insurers often require baseline controls, which pushes suppliers to have them.
- **Extra inventory** of critical supplies and materials.

**Resourcefulness**

- **Cross-train** staff so work continues when someone is out.
- **Share threat intelligence**, coordinate with **external** groups, use **adaptive** security tools.
- **Backup transportation routes** for physical goods.
- **Cyber insurance** itself, to pay for recovery.

**Redundancy**

- Extra inventory, **alternative manufacturing** facilities, **more than one vendor**.
- Hot and cold sites.
- **Backup communication channels**: if email is compromised, how do you reach your suppliers?

**Rapidity**

- **Backup recovery**, **spare equipment and parts**, multiple suppliers to switch to.
- **Incident response** that includes suppliers.
- **Automated alert systems**, for example when a vendor announces a breach.

## Containing a compromised vendor

- Give each vendor its **own** limited accounts and network access, so you can cut one off without breaking everything.
- Know **which systems run which vendor's products** (an inventory, sometimes called an SBOM, software bill of materials, for software).
- **Monitor** vendor connections like any other traffic: a signed update can still be malicious.

Next, a check.
