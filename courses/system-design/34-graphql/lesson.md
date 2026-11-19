# GraphQL, and Choosing a Style

*Chapter 1 · Foundations.*

## GraphQL: the client chooses the shape

**GraphQL** exposes one endpoint and a **schema**: a typed description of every object and field.

```graphql
type Query {
  book(id: Int!): Book
  books(limit: Int): [Book!]!
}

type Book { id: Int!  title: String!  year: Int  author: Author! }
type Author { id: Int!  name: String! }
```

The client sends a **query** naming exactly the fields it wants, nested as deep as it likes, and gets back JSON in exactly that shape:

```graphql
{
  books(limit: 2) {
    title
    author { name }
  }
}
```

```json
{"data": {"books": [
  {"title": "Kindred", "author": {"name": "Octavia Butler"}},
  {"title": "Parable of the Sower", "author": {"name": "Octavia Butler"}}
]}}
```

No over-fetching, no under-fetching, one round trip. That's why mobile apps on slow networks love it. Writes go through **mutations**, which look like queries with side effects.

The server **validates** every query against the schema before running anything: an unknown field is rejected with an error, and no data is returned. Then **resolvers** fetch each field.

### The N+1 problem

The naive way to resolve the query above runs one query for the list of books, then one more query *per book* for its author: **N+1 queries**. For a page of 50 books, that's 51 trips to the database. The fix is **batching**: collect every author id the page needs and load them in a single query. Facebook's **DataLoader** library does this automatically by deferring loads within one tick of the event loop.

GraphQL's costs: every query is a `POST` to one URL, so HTTP caching stops working and you need your own caching. A malicious or careless client can request an enormously deep query, so servers limit query depth and cost. And the server can't optimize for a fixed set of known requests.

## Choosing

| | REST | RPC (gRPC) | GraphQL |
|---|---|---|---|
| Models | Resources | Functions | A graph the client queries |
| Typical encoding | JSON | Protocol Buffers | JSON |
| Caching | HTTP caches just work | Your problem | Your problem |
| Fetch shape | Fixed per endpoint | Fixed per method | Chosen by the client |
| Best for | Public APIs, web resources | Internal service-to-service calls | Many client types with different data needs |

Many companies use all three: REST for partners, gRPC between internal services, and GraphQL as a gateway for their own apps.

Next, a short check on what you just read.
