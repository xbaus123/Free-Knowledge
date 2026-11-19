# Write Skew and Phantoms

*Chapter 7 · Transactions and Fault Tolerance.*

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

Next, a short check on what you just read.
