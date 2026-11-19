# Services for the System

*Chapter 2 · Part 1: Operating-System Services.*

The second family of services doesn't help any single user directly. It keeps a **shared** system fair, efficient, and safe.

## Resource allocation

When **multiple users or multiple jobs** run at the same time, resources must be **allocated to each of them**. There are many kinds:

- **CPU cycles**: who runs, and for how long?
- **Main memory**: who gets which addresses?
- **File storage**: who gets which disk blocks?
- **I/O devices**: who gets the printer or the camera right now?

Some of these need special allocation code (CPU scheduling is a whole chapter later). Others use a general request-and-release pattern.

## Accounting

**Accounting** keeps track of **which users use how much, and what kinds of computer resources**. The records can be used for billing, or simply for statistics that help administrators reconfigure the system.

## Protection and security

The owners of information in a **multiuser or networked** system may want to control who uses it, and **concurrent processes shouldn't interfere with each other**. Two related ideas:

| | Protection | Security |
|---|---|---|
| Guards against | Processes and users *inside* the system | Attackers *outside* the system |
| Means | Ensuring **all access to system resources is controlled** | **User authentication** (passwords, keys), plus defending external I/O devices from **invalid access attempts** |

A chain is only as strong as its weakest link: precautions have to cover the whole system.

That's every service. A check, then a drill that mixes both families.
