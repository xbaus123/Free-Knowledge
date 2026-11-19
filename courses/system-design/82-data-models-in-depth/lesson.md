# Relational and Document Models in Depth

*Chapter 3 · Data Models and Storage Engines.*

*Based on* Designing Data-Intensive Applications*, Chapters 2 and 4.*

Every application is layers of data models stacked on each other: your objects, the database's model of them, bytes on disk. The model you pick shapes what's easy and what's painful, often more than any other decision. The same goes for the API your services use to talk to each other. Chapter 1 introduced APIs and databases. These readings compare the models in depth and adds a third: the graph.

## The relational model

Data lives in **tables** (relations) of **rows** (tuples), queried with **SQL**. Relationships are expressed with **foreign keys** and recombined at query time with **joins**.

```sql
SELECT p.name, SUM(oi.quantity)
FROM customers c
JOIN orders o       ON o.customer_id = c.id
JOIN order_items oi ON oi.order_id = o.id
JOIN products p     ON p.sku = oi.sku
WHERE c.name = 'Ada'
GROUP BY p.name;
```

**Normalization** stores each fact once: a product's name lives only in `products`, and orders refer to it by ID. Renaming a product is one update, with no risk of copies disagreeing.

SQL is **declarative**. You say *what* you want, and the **query optimizer** decides *how*: which index, which join order. That's why the database can get faster without your code changing.

## The document model

Document databases (MongoDB, CouchDB, Firestore) store self-contained **documents**, usually JSON, with nested objects and arrays:

```json
{
  "_id": 1, "name": "Ada",
  "orders": [
    { "order_id": 1, "items": [
      { "sku": "KB-1", "name": "Mechanical Keyboard", "quantity": 1 },
      { "sku": "MS-1", "name": "Wireless Mouse", "quantity": 2 } ] }
  ]
}
```

Strengths:

- **Locality**: everything about a customer comes back in one read, with no joins. Great for **one-to-many** trees that are always loaded together, like a profile with its positions and education.
- **Less impedance mismatch**: the document looks like the objects in your code. With SQL, an ORM has to translate between nested objects and flat tables.
- **Schema-on-read**: the database doesn't enforce a structure. Readers interpret whatever is there, so changing a structure doesn't need a migration (but your code must handle old shapes).

Weaknesses show up with **many-to-one** and **many-to-many** relationships. Above, the product name is copied into every order (**denormalized**). Rename the product and you must update every copy. Questions that cut *across* documents, like "who else bought what Ada bought?", need multiple queries or `$lookup` joins that document stores handle less naturally.

Relational databases enforce **schema-on-write**: data must match the declared columns when it's written. It's like static vs. dynamic typing: neither is strictly better.

Next, a short check on what you just read.
