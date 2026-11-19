# Indexes and B-trees

*Chapter 1 · Foundations.*

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

The number of children per page is the **fanout**, and it's large, often several hundred. So B-trees are very shallow: with a fanout of 500, four levels address 500⁴ ≈ 62 billion keys. Finding any one of them takes four page reads, and the top levels are almost always cached in memory (earlier in this chapter).

Because the keys are sorted, B-trees also answer **range queries** (`WHERE created_at BETWEEN ...`) and **ordered results** (`ORDER BY`) by reading neighboring leaves. Chapter 3 shows how B-trees handle writes and crashes, and compares them with log-structured storage.

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

Next, a short check on what you just read.
