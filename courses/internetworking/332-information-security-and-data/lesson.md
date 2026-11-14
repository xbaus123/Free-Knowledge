# Information Security and Data

*Chapter 10 · Resilience.*

Networks exist to move **data**, and data needs resilience too. To think about it, this lesson borrows two tools: one from information security and one from information theory.

## The McCumber cube

John McCumber's model (1991) looks at information security as a **cube** with three sides:

| Side | The three options |
|---|---|
| **Information characteristics** (what you protect) | **Confidentiality**, **integrity**, **availability**: the CIA triad |
| **Information states** (where the data is) | **Transmission** (moving across the network), **storage** (at rest on disk), **processing** (in use, in memory) |
| **Security countermeasures** (how you protect it) | **Technology**, **policy and practice**, **education, training, and awareness** |

That's 3 × 3 × 3 = **27** small cubes, and each one is a question. For example: how do we protect the **integrity** of data in **transmission** with **technology**? (A hash or TLS.) How do we protect the **confidentiality** of data in **storage** through **training**? (Teach people not to leave files on USB sticks.)

The cube's point: it's easy to protect data in one state and forget another. Encrypted on the wire, but sitting in plain text on a backup tape.

## Information theory

The other side of the slide is information theory: describing data so you can tell **normal** from **abnormal**.

- **Descriptive statistics**: the **mean** (average), the **median** (middle value), and the **mode** (most common value). The mean is pulled by extreme values; the median isn't. A single huge spike moves the mean of a day's traffic, not its median.
- **Time**: data means different things at different times. 10,000 logins at 9 a.m. on a Monday is normal; at 3 a.m. on a holiday it isn't.
- **The six questions**: who, what, when, where, why, and how. A log entry that answers all six is far more useful in an incident than one that just says "error."

## Questions for data resilience

- Can we keep customer data **separate** from the different kinds of cloud hosting, so a problem in one doesn't expose all of it?
- How do we build **privacy and data protection** in **by design**, and comply with the laws that require it?
- What safeguards protect against **tampering**, **poisoning**, and compromise?
- Do we need to be **transparent** about our algorithms and how data is used?
- How can users **opt out**, or **correct** inaccurate data about them?
- What about the **right to be forgotten**: deleting someone's data on request, as Europe's **GDPR** requires? (Including from backups, which is harder than it sounds.)

Next, a check.
