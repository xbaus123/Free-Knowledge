# Serializability and the Anomaly Zoo

*Chapter 7 · Transactions and Fault Tolerance.*

## Serializability

The strongest level: any concurrent execution has the same result as *some* serial order. Three implementations:

1. **Actual serial execution**: run every transaction on a single thread (VoltDB, Redis). Transactions must be short and data must fit in memory, and you partition to scale.
2. **Two-phase locking (2PL)**: readers block writers and writers block readers, with locks held until commit, including **predicate locks** on search conditions to stop phantoms. It's correct, but slow and prone to deadlocks.
3. **Serializable snapshot isolation (SSI)**: transactions run optimistically on snapshots, and the database tracks what each one *read*. At commit, if something it read has since been changed by a committed transaction, its premise may be outdated, so it **aborts**. The application must **retry**. This is PostgreSQL's `SERIALIZABLE`.

## The anomaly zoo

| Anomaly | Read committed | Snapshot isolation | Serializable |
|---|---|---|---|
| Dirty read | Prevented | Prevented | Prevented |
| Dirty write | Prevented | Prevented | Prevented |
| Read skew | **Possible** | Prevented | Prevented |
| Lost update | **Possible** | Sometimes detected | Prevented |
| Write skew | **Possible** | **Possible** | Prevented |
| Phantom (write skew) | **Possible** | **Possible** | Prevented |

Right after the next two quizzes, you'll reproduce write skew in a booking system and fix it both ways: with `SELECT ... FOR UPDATE`, and with serializable isolation plus retries.

Next, a short check on what you just read.
