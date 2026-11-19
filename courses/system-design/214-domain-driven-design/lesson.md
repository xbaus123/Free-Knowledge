# Finding Boundaries with Domain-Driven Design

*Chapter 9 · Microservices and Data Flow.*

## Finding boundaries: Domain-Driven Design

Where you cut matters more than whether you cut. Cut in the wrong place, and every feature touches four services and every request crosses the network ten times. **Domain-Driven Design (DDD)**, from Eric Evans's 2003 book, gives the vocabulary for finding good boundaries.

### Bounded contexts

In a large business, the same word means different things to different people. To sales, a **customer** is a lead with a pipeline stage. To billing, it's a payment method and an invoice history. To support, it's a ticket history and a satisfaction score. A **product** in the catalog has photos and descriptions. In the warehouse, it has a shelf location and a weight.

Trying to build one `Customer` model for everyone produces a giant, fragile class that every team must change. DDD instead defines **bounded contexts**: areas of the business with their own consistent model and their own **ubiquitous language** (the shared vocabulary of that context's domain experts and engineers). Each context has its own `Customer`, holding only what it needs, linked to the others by a shared id. **A bounded context is the natural boundary for a service**, or for a small group of services owned by one team.

### Aggregates

Inside a context, an **aggregate** is a cluster of objects that must stay consistent together, with one **root** that all changes go through. An `Order` with its line items is an aggregate: the total must always match the items. DDD's rules:

- A transaction modifies **one aggregate**.
- Aggregates refer to each other **by id**, not by object reference.
- Consistency *between* aggregates is **eventual**, through events.

These rules are what make splitting possible. If no transaction ever spans two aggregates, aggregates can live in different databases, or different services, without distributed transactions.

### Good boundaries

- **Split by business capability** (ordering, payments, inventory, shipping), not by technical layer. A "database service" or a "validation service" that every other service calls is a bottleneck in disguise.
- **High cohesion, low coupling**: things that change together stay together. If every feature needs coordinated changes to two services, they're one service.
- **Database per service**: each service owns its tables, and nobody else reads them directly. A shared database is hidden coupling: one team's schema change breaks another's queries, and nobody can tell who depends on what. Data needed elsewhere is shared through APIs, or published as **events** that other services use to build their own **derived** read models (later in this chapter).
- **Translate at the edges**: when your context consumes another's model (especially a legacy system or a vendor), wrap it in an **anti-corruption layer** that translates their concepts into yours, so their quirks don't leak through your code.

To migrate a monolith, use the **strangler fig** pattern (named after a vine that grows around a tree until it replaces it): put a proxy (chapter 2) in front of the monolith, then route one capability at a time to new services, until nothing is left.

Next, a short check on what you just read.
