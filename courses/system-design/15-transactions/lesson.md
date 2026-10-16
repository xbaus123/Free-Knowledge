# Transactions and the Anomaly Zoo

*Based on* Designing Data-Intensive Applications*, Chapter 7.*

Many things can go wrong while your application changes data: the database crashes halfway through, the network drops, two clients write the same record at once, or a client reads data that's only half updated. A **transaction** groups several reads and writes into one logical unit that either **commits** entirely or **aborts** entirely, so the application doesn't have to handle every partial failure itself.

## ACID

| Letter | Meaning | What it really guarantees |
|---|---|---|
| **A**tomicity | All or nothing | If the transaction aborts (a crash, a constraint violation), every write in it is undone, so it's safe to retry. Better named *abortability*. |
| **C**onsistency | Invariants hold | Your application's rules (accounts balance, no double bookings) stay true. This depends on the *application*; the database only enforces the constraints you declare. |
| **I**solation | Concurrent transactions don't interfere | Ideally **serializable**: the result is as if the transactions ran one at a time. Most databases default to something weaker. |
| **D**urability | Committed data survives | It's written to disk (and the write-ahead log), or replicated, before the commit is confirmed. |

Isolation is where things get subtle. Serializability costs performance, so databases offer **weaker isolation levels**, each of which allows some **anomalies**. Bugs from these anomalies are rare, timing-dependent, and have cost real money.

## Read committed

The most basic level, and the default in PostgreSQL and Oracle. It prevents two anomalies:

- **Dirty reads**: seeing another transaction's uncommitted writes. If it later aborts, you acted on data that never existed.
- **Dirty writes**: overwriting another transaction's uncommitted write. Databases prevent these with row-level write locks held until commit.

## Snapshot isolation

Read committed still allows **read skew** (a nonrepeatable read). Alice has $500 in each of two accounts, and a transfer moves $100 between them. If she reads account 1 before the transfer and account 2 after it, she sees $900 in total, and $100 seems to have vanished. Backups and analytics queries that run for a long time are especially vulnerable.

**Snapshot isolation** gives each transaction a **consistent snapshot** of the whole database as of when it started. It's implemented with **multi-version concurrency control (MVCC)**: the database keeps several committed versions of each row, and each transaction sees the versions that were committed when it started. *Readers never block writers, and writers never block readers.* PostgreSQL calls this level *repeatable read*.

## Lost updates

Two transactions **read-modify-write** the same value concurrently, such as incrementing a counter or editing a document. The second write overwrites the first, and one update is lost. Fixes:

- **Atomic operations**: `UPDATE counters SET value = value + 1 WHERE key = 'x'`.
- **Explicit locking**: `SELECT ... FOR UPDATE` locks the rows you read until your transaction ends. A concurrent transaction that tries the same waits for you to commit, then sees your result.
- **Automatic detection**: some databases abort the transaction that would lose an update (PostgreSQL's repeatable read does).
- **Compare-and-set**: `UPDATE ... SET content = 'new' WHERE id = 1 AND content = 'old'`. If nothing matches, someone else changed it first, so retry.

## Write skew and phantoms

The subtlest anomaly. A hospital requires at least one doctor on call. Alice and Bob are both on call and both feel ill. At the same moment, each runs:

```sql
SELECT count(*) FROM doctors WHERE on_call = true AND shift_id = 1234;  -- 2, so it's safe to leave
UPDATE doctors SET on_call = false WHERE name = 'Alice' AND shift_id = 1234;  -- (Bob's transaction updates Bob)
```

Each transaction saw two doctors on call, so each let its doctor go. Both commit, and nobody is on call. Neither transaction overwrote the other's data, so this isn't a dirty write or a lost update. It's **write skew**:

1. Read some rows and check a condition.
2. Decide based on the result.
3. Write. The write changes the result of step 1 for the other transaction, but neither sees the other's write.

It's everywhere: booking a meeting room, claiming a username, spending a balance from two devices, or booking a golf simulator bay.

When the condition checks for the **absence** of rows ("no booking overlaps 18:00–19:00"), it's worse: there's no row to lock, because the conflicting row doesn't exist yet. A write that changes the result of another transaction's search is a **phantom**. `SELECT ... FOR UPDATE` can't lock a row that isn't there.

Fixes for write skew:

- **Lock something that does exist**: lock the parent row (the doctor's shift, the room, the bay) with `FOR UPDATE` before checking. Every transaction touching that resource now runs one at a time. If no such row exists, you can create one just to lock (**materializing conflicts**), but that's a last resort.
- **Constraints**: a unique index stops two identical bookings, but can't express "no *overlapping* time ranges" in most databases.
- **Serializable isolation**.

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

In the next lesson, you'll reproduce write skew in a booking system and fix it both ways: with `SELECT ... FOR UPDATE`, and with serializable isolation plus retries.
