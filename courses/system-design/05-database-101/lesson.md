# Database 101: Tables, Indexes, and ACID

*Part I · Foundations.*

Almost every system in this course is, at its heart, a way of storing data and getting it back. A **database** does far more than write bytes to a file. It enforces rules about what data may look like, finds things quickly among billions of records, and keeps data correct when many clients change it at once or the power fails halfway through. This lesson covers the three ideas you'll lean on constantly: **data models**, **indexes**, and **transactions**.

## The relational model

A relational database stores data in **tables**. Each **row** is one record, and each **column** has a name and a type. You query it with **SQL**:

```sql
SELECT name, email FROM users WHERE id = 1;
```

### Keys and relationships

- A **primary key** uniquely identifies each row: `users.id`.
- A **foreign key** is a column that refers to another table's primary key: `accounts.user_id` points at `users.id`. It's how tables relate.
- A **join** recombines related rows at query time:

```sql
SELECT u.name, a.id, a.balance
FROM users u
JOIN accounts a ON a.user_id = u.id
WHERE u.email = 'ada@example.com';
```

### Constraints: let the database say no

**Constraints** are rules the database enforces on every write, no matter which program or person makes it:

| Constraint | Guarantees |
|---|---|
| `PRIMARY KEY` | Every row has a unique id |
| `NOT NULL` | The column always has a value |
| `UNIQUE` | No two rows share the value (two users can't have one email) |
| `REFERENCES` (foreign key) | The row it points to exists |
| `CHECK (balance >= 0)` | Any condition you can write about the row |

Application code has bugs, and there's always more than one application: a migration script, an admin tool, a new service next year. A constraint in the database holds for all of them. A write that would break one fails with an error, and nothing changes.

### Normalization

**Normalization** means storing each fact exactly once. A user's email lives in one row of `users`, and everything else refers to the user by id. Change the email once, and every account, order, and transfer sees the change. Copying the email into every account row (**denormalizing**) makes some reads faster, but every copy is one more place that can disagree.

## The document model

Document databases (MongoDB, Firestore, CouchDB) store each record as a nested **document**, usually JSON:

```json
{
  "id": 1, "name": "Ada", "email": "ada@example.com",
  "accounts": [{"id": 10, "balance": 500}, {"id": 11, "balance": 20}]
}
```

- **Embedding** related data in one document gives you **locality**: one read returns the whole thing, with no joins. It fits data that's naturally a tree and always loaded together.
- There's no fixed schema: each document can have its own shape (**schema-on-read**). That's flexible, but your code has to cope with every shape ever written.
- Relationships *between* documents (many-to-one, many-to-many) are weaker. Joins are limited or missing, so you either copy data around or make several queries.

| | Relational | Document |
|---|---|---|
| Unit | Rows in flat tables | Nested documents |
| Relationships | Foreign keys and joins | Embedding, or references resolved in application code |
| Schema | Enforced on write | Interpreted on read |
| Strength | Integrity, flexible queries across data | Locality, matching the shape of your objects |

The boundary is blurry: PostgreSQL stores and indexes JSON, and MongoDB has joins and schema validation. Lessons 8 and 9 compare relational, document, and graph models in depth.

## Indexes

Without help, a database answers `WHERE user_id = 1` with a **full table scan**: read every row and check it. For a million rows that's a million checks, every time.

An **index** is an extra data structure, kept up to date alongside the table, that maps column values to the rows that have them. It's the index at the back of a book: you look up a word and jump to the page.

### B-trees

The index in nearly every relational database is a **B-tree**:

- The keys are kept **sorted**, divided into fixed-size **pages** (often 4 to 16 KB, the unit the disk reads).
- An **internal page** holds hundreds of keys that split the key space into ranges, each with a pointer to a child page. **Leaf pages** hold the keys themselves with pointers to their rows.
- A lookup starts at the root and follows one pointer per level down to a leaf.

```text
                    [ 300 | 600 ]                      root
          /               |               \
   [ 100 | 200 ]     [ 400 | 500 ]     [ 700 | 800 ]    internal pages
    /    |    \       ...                  ...
 leaves with the keys, in order, pointing to rows
```

The number of children per page is the **fanout**, and it's large, often several hundred. So B-trees are very shallow: with a fanout of 500, four levels address 500⁴ ≈ 62 billion keys. Finding any one of them takes four page reads, and the top levels are almost always cached in memory (lesson 3).

Because the keys are sorted, B-trees also answer **range queries** (`WHERE created_at BETWEEN ...`) and **ordered results** (`ORDER BY`) by reading neighboring leaves. Lesson 10 shows how B-trees handle writes and crashes, and compares them with log-structured storage.

### Composite indexes

An index can cover several columns. An index on `(from_account, created_at)` is sorted by `from_account`, and by `created_at` within each account. That makes this query fast twice over:

```sql
SELECT * FROM transfers
WHERE from_account = 10
ORDER BY created_at DESC
LIMIT 10;
```

The database jumps to account 10's entries, and they're already in time order, so it reads the last ten and stops, with no sort. Column order matters: the index helps queries that filter on its **leftmost** columns. It's useless for `WHERE created_at > ...` alone, just as a phone book sorted by last name, then first name, can't find everyone named "Ada."

### Indexes aren't free

Every index speeds up some reads and slows down **every** write to its table, because each insert, update, and delete must update the index too. Indexes also take space. Add the ones your important queries need, and no more.

`UNIQUE` and `PRIMARY KEY` constraints create an index automatically, since checking uniqueness quickly needs one.

### Reading the query plan

Don't guess whether a query uses an index. Ask the database:

```sql
EXPLAIN QUERY PLAN SELECT * FROM accounts WHERE user_id = 1;
```

| Plan line (SQLite) | Means |
|---|---|
| `SCAN accounts` | Full table scan |
| `SEARCH accounts USING INDEX accounts_by_user (user_id=?)` | Index lookup |
| `USE TEMP B-TREE FOR ORDER BY` | The results had to be sorted after fetching them |

PostgreSQL and MySQL have `EXPLAIN` too, with their own vocabulary for the same ideas.

## Transactions and ACID

A bank transfer is several writes: debit one account, credit another, record the transfer. What if the process crashes after the debit? What if two transfers from the same account run at once? A **transaction** groups writes into one unit, and the database promises four properties, **ACID**:

- **Atomicity**: all of the transaction's writes happen, or none do. If anything fails partway, the database **rolls back** every write the transaction made. You never see half a transfer.
- **Consistency**: the data moves from one valid state to another, respecting every constraint. A transaction that would leave a negative balance fails as a whole. (Strictly, keeping data valid is your application's job, and atomicity and constraints are the database's tools for helping.)
- **Isolation**: concurrent transactions don't see each other's half-finished work. Ideally, the result is as if they had run one at a time. In practice databases offer weaker, faster **isolation levels**, and their anomalies fill lessons 19 and 20.
- **Durability**: once the database says "committed," the data survives a crash. It's written to a **write-ahead log** and `fsync`ed to disk before the commit returns (lesson 3).

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

That completes the foundations. Next, you'll put numbers on a system's load with back-of-the-envelope estimates.
