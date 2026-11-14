# Reliability and Availability

*Chapter 10 · Resilience.*

Resilience is about surviving incidents. **Reliability** is about how often things fail in the first place, and it supports resilience: the fewer failures, the fewer incidents to survive.

## Reliability

**Reliability** is the **probability** that a system will perform its stated requirements, in a stated environment, over a stated period of time.

All three "stated" parts matter. "This router is reliable" says nothing. "This router has a 99% chance of running a year without failure, in a cooled server room, at up to 80% load" is a reliability claim you can test.

Reliability is usually measured with **success and failure rates**, and with:

- **MTBF**, mean time between failures: on average, how long it runs before failing.
- **MTTR**, mean time to repair (or recover): on average, how long a failure lasts.

## Reliability is not availability

**Availability** is the fraction of time the system is up:

```
availability = MTBF / (MTBF + MTTR)
```

They're related, but not the same. A server that crashes **every day** but restarts in **5 seconds** has poor reliability and excellent availability. A server that fails **once a year** but takes **a week** to fix is very reliable, and its availability is only about 98%.

Availability is often given in **nines**:

| Availability | Downtime per year |
|---|---|
| 99% ("two nines") | about 3.65 days |
| 99.9% ("three nines") | about 8.76 hours |
| 99.99% ("four nines") | about 52.6 minutes |
| 99.999% ("five nines") | about 5.26 minutes |

Each extra nine is ten times less downtime, and usually costs a lot more.

## Series and parallel

Systems are built from parts, and how they're connected changes the total:

- **Series**: every part must work (a request passes the firewall, **then** the web server, **then** the database). Multiply: two 99% parts give 0.99 × 0.99 = **98.01%**. A chain is weaker than its weakest link.
- **Parallel**: any one part is enough (two web servers behind a load balancer). It fails only if **all** fail: 1 - (0.01 × 0.01) = **99.99%**.

This is the math behind redundancy, and behind avoiding **single points of failure**.

## Fault versus failure

- A **fault** is a defect or cause: a bad memory chip, a bug, a loose cable.
- A **failure** is when the system **stops delivering** what it should.

A fault doesn't have to become a failure. A bit flipped by a bad memory chip, caught and corrected by ECC memory, is a fault with no failure. **Fault tolerance** is exactly that: faults happen, failures don't.

## The limits of reliability models

The math above works well for **complicated** systems: many parts, but predictable ones, like a jet engine or a RAID array. You can list the parts and multiply.

It works badly for **complex** systems, where parts **interact** in ways nobody fully predicts: a large network with people, vendors, and attackers in it. Failures there come from unexpected combinations, and an attacker doesn't fail at random like a disk does. That's why reliability **supports** resilience but can't replace it.

Next, a check.
