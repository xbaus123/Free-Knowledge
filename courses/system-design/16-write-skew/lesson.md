# Write Skew: Double-Booking the Golf Simulator

Your indoor golf facility rents simulator bays by the hour. On Friday evenings, two customers sometimes book **the same bay at the same time** and both get a confirmation. Then they both show up.

The booking code looks reasonable:

```python
with db.transaction() as tx:
    clash = tx.execute(
        "SELECT id FROM bookings WHERE bay_id = ? AND start_min < ? AND end_min > ?",
        (bay, end, start))
    if clash:
        return False
    tx.execute("INSERT INTO bookings (bay_id, start_min, end_min, customer) VALUES (?, ?, ?, ?)",
               (bay, start, end, customer))
    return True
```

It runs in a transaction, under the default **READ COMMITTED** isolation. Two concurrent transactions both run the `SELECT`, both see no overlapping booking, and both `INSERT`. This is **write skew** with a **phantom**: the row that should have stopped each transaction is the one the *other* transaction was about to create.

## The files

- **`minidb.py`** (read-only): a small in-memory SQL database that behaves like PostgreSQL where it matters. It has transactions, row locks with `SELECT ... FOR UPDATE`, and two isolation levels, `"read committed"` and `"serializable"`. The top of the file lists the SQL it understands.
- **`shop.py`** (read-only): creates the facility's tables.

  ```text
  bays(id, name)
  bookings(id, bay_id, start_min, end_min, customer)
  ```

  Times are minutes after midnight (18:00 is 1080), and a booking covers `[start, end)`, so 18:00–19:00 and 19:00–20:00 don't clash.
- **`race.py`** (read-only): `run_concurrently(db, calls)` runs bookings on threads in the **worst-case interleaving**. Each one pauses after its first `SELECT` until the others have reached theirs. The tests use it so the race happens every time, not one run in a thousand.
- **`booking.py`**: yours. `book_unsafe` is the original flow; leave it alone, since the first test uses it to reproduce the bug.

## Your task

Fix the bug two ways.

### 1. `book_with_lock`: an explicit lock

Stay on READ COMMITTED, but make concurrent bookings of the **same bay** take turns.

`SELECT ... FOR UPDATE` locks the rows it returns until your transaction ends, and another transaction trying to lock them waits. But you can't lock the clashing booking, because it doesn't exist yet. Lock something that *does* exist and that every booking of this bay must touch first.

The tests check that:

- Only one of several racing bookings succeeds, for both identical and overlapping times.
- Bookings of **different** bays don't wait for each other. Lock only what you need.

### 2. `book_serializable`: serializable isolation

Now use no explicit locks at all. Open the transaction with:

```python
db.transaction(isolation="serializable")
```

Serializable transactions read from a snapshot, and the database remembers what each one *searched for*. At commit, if a concurrent transaction has committed a row that would have changed your search results, your commit fails with `minidb.SerializationFailure`. That's how PostgreSQL's serializable snapshot isolation works.

Your code must catch the failure and **retry the whole transaction**. On the retry, it sees the other booking and correctly returns `False`. Give up after `attempts` tries by letting the error propagate.

## Think about it

- Which fix holds locks while the customer's request runs? Which one does wasted work instead?
- A **unique index** on `(bay_id, start_min)` would stop identical bookings. Why doesn't it stop 18:00–19:30 overlapping 19:00–20:00? (PostgreSQL can enforce non-overlapping ranges with an *exclusion constraint*; most databases can't.)
- The doctors-on-call example from the last lesson has the same shape. What would you lock there?
