# The Document Model

*Chapter 1 · Foundations.*

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

The boundary is blurry: PostgreSQL stores and indexes JSON, and MongoDB has joins and schema validation. Chapter 3 compares relational, document, and graph models in depth.

Next, a short check on what you just read.
