# Snapshot Isolation and Lost Updates

*Chapter 7 · Transactions and Fault Tolerance.*

## Snapshot isolation

Read committed still allows **read skew** (a nonrepeatable read). Alice has $500 in each of two accounts, and a transfer moves $100 between them. If she reads account 1 before the transfer and account 2 after it, she sees $900 in total, and $100 seems to have vanished. Backups and analytics queries that run for a long time are especially vulnerable.

**Snapshot isolation** gives each transaction a **consistent snapshot** of the whole database as of when it started. It's implemented with **multi-version concurrency control (MVCC)**: the database keeps several committed versions of each row, and each transaction sees the versions that were committed when it started. *Readers never block writers, and writers never block readers.* PostgreSQL calls this level *repeatable read*.

## Lost updates

Two transactions **read-modify-write** the same value concurrently, such as incrementing a counter or editing a document. The second write overwrites the first, and one update is lost. Fixes:

- **Atomic operations**: `UPDATE counters SET value = value + 1 WHERE key = 'x'`.
- **Explicit locking**: `SELECT ... FOR UPDATE` locks the rows you read until your transaction ends. A concurrent transaction that tries the same waits for you to commit, then sees your result.
- **Automatic detection**: some databases abort the transaction that would lose an update (PostgreSQL's repeatable read does).
- **Compare-and-set**: `UPDATE ... SET content = 'new' WHERE id = 1 AND content = 'old'`. If nothing matches, someone else changed it first, so retry.

Next, a short check on what you just read.
