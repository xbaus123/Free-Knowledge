# Database 101: Tables, Indexes, and ACID

*Chapter 1 · Foundations.*

Build a small bank in SQLite with what the last four readings covered: constraints, indexes, an atomic transfer, and a nested document.

## Your task

`solution.py` builds a small bank in SQLite. Every function gets `conn`, a `sqlite3` connection with foreign key checks turned on (SQLite leaves them off by default).

### 1. The schema

`create_schema(conn)` creates three tables. `users` is done. Finish the others, with every rule enforced by a constraint:

```text
users     (id INTEGER PRIMARY KEY, email TEXT, required and unique, name TEXT, required)
accounts  (id INTEGER PRIMARY KEY, user_id → users.id, required,
           balance INTEGER, required, never negative)
transfers (id INTEGER PRIMARY KEY, from_account → accounts.id, required,
           to_account → accounts.id, required, amount INTEGER, required, positive,
           created_at TEXT, required)
```

The tests try to insert bad rows, and every one must fail.

### 2. Indexes

`add_indexes(conn)` makes these queries run without a table scan or a sort, using at most three indexes in total (the tests read `EXPLAIN QUERY PLAN`):

```sql
SELECT * FROM accounts WHERE user_id = ?
SELECT * FROM transfers WHERE from_account = ? ORDER BY created_at DESC LIMIT 10
```

### 3. An atomic transfer

`transfer(conn, from_id, to_id, amount, created_at)` currently commits after each statement. A failure halfway leaves money missing. Make it all or nothing:

- Do all three writes in one transaction, and commit at the end.
- If either account doesn't exist, raise `ValueError`. Nothing may change.
- If the source can't cover the amount, or the amount isn't positive, your constraints raise `sqlite3.IntegrityError`. Let it propagate, with everything rolled back.

The tests check from a second connection: committed transfers must be visible there, and failed ones must leave no trace.

### 4. Relational to document

`user_document(conn, user_id)` assembles a user and their accounts (in id order) into the nested document shown earlier, or returns `None` for a missing user.

### 5. B-tree height

`btree_height(rows, fanout)` returns the fewest levels with `fanout ** levels >= rows`, and at least 1. Try it in the **Scratchpad**: how many levels do a billion rows need with a fanout of 500? With a fanout of 2, like a binary tree?

## Key terms

| Term | Meaning |
|---|---|
| Primary key | The column that uniquely identifies each row |
| Foreign key | A column that refers to another table's primary key |
| Constraint | A rule the database enforces on every write |
| Normalization | Storing each fact once and referring to it by id |
| Full table scan | Reading every row to answer a query |
| Index | An extra, always-updated structure that finds rows by value |
| B-tree | A shallow, sorted tree of pages: the standard database index |
| Fanout | How many children each B-tree page points to |
| Composite index | An index on several columns, sorted by the leftmost first |
| Transaction | A group of writes that commit or roll back together |
| ACID | Atomicity, consistency, isolation, durability |

Next, you'll put numbers on a system's load with back-of-the-envelope estimates.
