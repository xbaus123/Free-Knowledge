# The Relational Model

*Chapter 1 · Foundations.*

Almost every system in this course is, at its heart, a way of storing data and getting it back. A **database** does far more than write bytes to a file. It enforces rules about what data may look like, finds things quickly among billions of records, and keeps data correct when many clients change it at once or the power fails halfway through. The next four readings cover the three ideas you'll lean on constantly: **data models**, **indexes**, and **transactions**.

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

Next, a short check on what you just read.
