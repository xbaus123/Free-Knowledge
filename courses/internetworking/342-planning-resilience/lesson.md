# Project: Plan for Resilience

*Chapter 10 · Resilience.*

Chapters 2 to 9 designed your project network and site: rooms and cables, switches and VLANs, subnets and routing, DNS, mail, and the website. This chapter's group assignment: **how will you address robustness and resourcefulness?** You may already have done some of it, like the backup plan in chapter 9. If so, just point to it.

## Robustness: what will you do so the site keeps working under attack?

**1. Patching and updates.** Who patches which systems, how often, and how do you know it's done? Include the **firmware** on routers, switches, access points, and cameras, not just servers.

**2. Hardware.** Enterprise-grade servers? RAID, and which level? Locked closets and tamper seals?

**3. Network defenses.** Firewalls, IDS or IPS, **segmentation** between your VLANs and subnets (chapters 3 and 5), and what each zone may reach.

**4. Access and privilege.** MFA for admins, **least privilege** for services, and which components **fail closed**.

**5. People.** Security awareness training, and how staff are alerted when an attack is going around.

**6. Monitoring.** What's logged, where the logs go, and who looks at them.

## Resourcefulness: when something breaks, what comes first?

**7. Priorities.** List your services in the order they come back. Routing and DNS first? Checkout before the blog?

**8. People.** Who can restore each critical system? Make sure the answer is never just one person.

**9. Outside help.** Vendor support contracts, an incident response firm, your ISP's emergency line. Write the numbers down **somewhere that isn't on the network that's down**.

**10. Spare capacity.** Which servers could take over another's job? Could DNS, DHCP, and logging run on more than one?

## A worked example

The chapter 9 shop, `shop.example.com`:

| Area | Choice |
|---|---|
| Patching | OS updates weekly on Tuesday night; firmware checked monthly against vendor advisories; signatures verified before install |
| Hardware | Two app servers, RAID 1 boot drives; database on RAID 1 too; closet locked with badge access and tamper seals on the firewall |
| Network | Firewall between DMZ, app, and database subnets; database reachable **only** from app servers on 5432; IDS on the DMZ |
| Access | MFA for all admin logins; services run as non-root users; the firewall fails closed |
| People | Phishing training twice a year; a staff chat channel for security alerts |
| Monitoring | All logs to a central log server; alerts for failed logins and CPU outside the meta-state baselines |
| Priorities | 1. Firewall and routing 2. DNS 3. Database 4. Checkout 5. Product pages 6. Everything else |
| People and help | Two admins trained on every restore; an IT support firm on retainer with a 1-hour response; printed contact sheet in the office safe |
| Spare capacity | DNS on two servers; either app server can run the whole shop at reduced speed |

Next, a check on planning for resilience.
