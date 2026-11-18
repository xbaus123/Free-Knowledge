# Cloud Computing

*Chapter 1 · Part 7: Computing Environments.*

**Cloud computing** **delivers computing, storage, and even apps as a service across a network**. Instead of buying servers, you rent them, and pay for what you use.

## Built on virtualization

Cloud computing is a **logical extension of virtualization**, because it **uses virtualization as the base for its functionality**. **Amazon EC2**, for example, has **thousands of servers, millions of virtual machines**, and **petabytes of storage** available across the Internet, and customers **pay based on usage**.

## Who can use it

| Type | Who it's for |
|---|---|
| **Public cloud** | Available via the Internet to **anyone willing to pay** |
| **Private cloud** | **Run by a company for the company's own use** |
| **Hybrid cloud** | Includes **both public and private** cloud components |

## What you get

| Service | What it provides | Example |
|---|---|---|
| **SaaS**: Software as a Service | One or more **applications** available via the Internet | A word processor in your browser |
| **PaaS**: Platform as a Service | A **software stack ready for application use** via the Internet | A database server |
| **IaaS**: Infrastructure as a Service | **Servers or storage** available over the Internet | Storage available for backup use |

A quick way to tell them apart: SaaS gives you a finished **app**, PaaS gives you a **platform** to build your app on, IaaS gives you raw **machines and disks**.

## Inside a cloud

Cloud environments are **composed of traditional OSes, plus VMMs, plus cloud management tools**.

```
              Internet ─ ─ ─ customer requests ─ ─ ─►  cloud customer interface
                 │                                            ┆ cloud management
             firewall ────────────────────────────────────────┤ commands
                 │                                            ┆
           load balancer                                      ┆
                 │                                            ▼
   ┌─ virtual machines ─ virtual machines ─ storage ─ cloud management services ─┐
   │     (servers)          (servers)                                            │
   └──────────────────────────────────────────────────────────────────────────────┘
```

- **Internet connectivity requires security** like **firewalls**.
- **Load balancers** **spread traffic across multiple applications**.
- Customers use a **cloud customer interface** to request resources, and **cloud management services** carry out those commands: starting VMs, allocating storage.

Next, a check on cloud computing.
