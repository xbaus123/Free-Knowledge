# Transactions and ACID

*Chapter 1 · Foundations.*

## Transactions and ACID

A bank transfer is several writes: debit one account, credit another, record the transfer. What if the process crashes after the debit? What if two transfers from the same account run at once? A **transaction** groups writes into one unit, and the database promises four properties, **ACID**:

- **Atomicity**: all of the transaction's writes happen, or none do. If anything fails partway, the database **rolls back** every write the transaction made. You never see half a transfer.
- **Consistency**: the data moves from one valid state to another, respecting every constraint. A transaction that would leave a negative balance fails as a whole. (Strictly, keeping data valid is your application's job, and atomicity and constraints are the database's tools for helping.)
- **Isolation**: concurrent transactions don't see each other's half-finished work. Ideally, the result is as if they had run one at a time. In practice databases offer weaker, faster **isolation levels**, and their anomalies fill chapter 7.
- **Durability**: once the database says "committed," the data survives a crash. It's written to a **write-ahead log** and `fsync`ed to disk before the commit returns (earlier in this chapter).

In SQL:

```sql
BEGIN;
UPDATE accounts SET balance = balance - 50 WHERE id = 10;
UPDATE accounts SET balance = balance + 50 WHERE id = 20;
INSERT INTO transfers (from_account, to_account, amount, created_at) VALUES (10, 20, 50, '2024-01-01T09:00');
COMMIT;      -- or ROLLBACK; to undo all of it
```

In Python's `sqlite3`, using the connection as a context manager does the same thing. It commits if the block finishes and rolls back if it raises:

```python
with conn:
    conn.execute("UPDATE ...")
    conn.execute("UPDATE ...")
```

An `UPDATE` that matches no rows isn't an error in SQL. It just changes nothing. Check `cursor.rowcount` to know how many rows a statement changed.

Next, a short check on what you just read.
