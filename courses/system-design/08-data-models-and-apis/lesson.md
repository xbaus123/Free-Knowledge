# Data Models and API Design

*Based on* Designing Data-Intensive Applications*, Chapters 2 and 4.*

Every application is layers of data models stacked on each other: your objects, the database's model of them, bytes on disk. The model you pick shapes what's easy and what's painful, often more than any other decision. The same goes for the API your services use to talk to each other. Lessons 4 and 5 introduced APIs and databases. This lesson compares the models in depth and adds a third: the graph.

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

## The graph model

When many-to-many relationships are the *point* of your data (social networks, road maps, fraud rings, recommendations), model them as a **graph**: **vertices** (nodes) and **edges** (relationships), both with properties. Neo4j's **Cypher** query language reads like a drawing of the pattern:

```cypher
MATCH (ada:Customer {name: 'Ada'})-[:PLACED]->(:Order)-[:CONTAINS]->(p:Product)
      <-[:CONTAINS]-(:Order)<-[:PLACED]-(other:Customer)
WHERE other <> ada
RETURN DISTINCT other.name
```

A **traversal** walks from vertex to vertex along edges. Queries of variable depth ("friends of friends of friends", "every part inside this assembly") are natural in a graph and awkward in SQL, which needs recursive common table expressions.

## Choosing

| Relationship shape | Good fit |
|---|---|
| Self-contained trees loaded together | Document |
| Many-to-one and many-to-many, ad hoc queries, strong integrity | Relational |
| Highly connected data, multi-hop traversals | Graph |

The lines blur: PostgreSQL stores JSON documents, and MongoDB supports joins. In the next lesson you'll answer the same two questions in all three models and feel where each fits.

## API design: how services talk

Data also flows *between* processes: from browser to server, and from service to service. A recap of the two dominant styles from lesson 4:

### REST

Built on HTTP's own concepts: **resources** identified by URLs, manipulated with standard methods.

| Method | Meaning | Idempotent? |
|---|---|---|
| `GET /orders/42` | Read | Yes |
| `PUT /orders/42` | Create or replace | Yes |
| `DELETE /orders/42` | Delete | Yes |
| `POST /orders` | Create (or perform an action) | No |

**Idempotent** means doing it twice has the same effect as once, which makes retries after timeouts safe. Use **status codes** (`200`, `201`, `404`, `409 Conflict`, `429 Too Many Requests`, `503`), **pagination** (`?cursor=…&limit=50`) for lists, and **versioning** (`/v2/…` or a header) for breaking changes. REST shines for public APIs: it's cacheable, debuggable with curl, and understood by every proxy.

### RPC

**Remote procedure calls** make a network request look like calling a function: `orders.Get(ctx, {id: 42})`. Modern frameworks like **gRPC** (Protocol Buffers over HTTP/2) and Thrift generate client and server code from an interface definition, with compact binary encoding and streaming.

The pitfall is pretending a network call is a local call. It isn't:

- It can **time out** with no way to know whether the request ran.
- Retries can run it **twice**, unless it's idempotent (use idempotency keys).
- It's slower, and its latency varies widely.
- Arguments must be **encoded** into bytes, and both sides may run different code versions.

RPC is great *inside* an organization, where you control both ends and want speed and generated types. REST dominates public APIs. **GraphQL** lets clients ask for exactly the fields they need in one request, which is handy for mobile apps aggregating many resources.

## Key terms

| Term | Meaning |
|---|---|
| Normalization | Each fact stored once, referenced by ID |
| Denormalization | Copies of data kept where they're read, to avoid joins |
| Impedance mismatch | Friction translating between application objects and the storage model |
| Schema-on-read / on-write | Structure interpreted when read / enforced when written |
| Traversal | Following edges from vertex to vertex in a graph |
| Idempotent | Safe to apply more than once |
