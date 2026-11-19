# The Graph Model, and Choosing a Model

*Chapter 3 · Data Models and Storage Engines.*

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

The lines blur: PostgreSQL stores JSON documents, and MongoDB supports joins. Next, after a short check, you'll answer the same two questions in all three models and feel where each fits.

Next, a short check on what you just read.
