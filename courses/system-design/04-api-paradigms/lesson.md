# API Paradigms: REST, RPC, and GraphQL

*Part I · Foundations.*

An **API** is a contract: what a caller may ask for, how to ask, and what comes back. Inside one program, that contract is a function signature. Between programs it's a **protocol** over the network, and the network brings everything from lesson 2: latency, lost requests, retries, and two sides that upgrade at different times.

Three styles cover most of what you'll meet. They differ in what they model: **REST** models *resources*, **RPC** models *function calls*, and **GraphQL** models *a graph of data the client can query*.

## HTTP in one minute

All three usually travel over HTTP. A request is a **method**, a **path**, **headers**, and an optional **body**. A response is a **status code**, headers, and a body:

```http
POST /books HTTP/1.1
Host: api.example.com
Content-Type: application/json
Idempotency-Key: 6f1c2a

{"title": "Kindred", "author_id": 1}
```

```http
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 8, "title": "Kindred", "author_id": 1, "year": null}
```

Status codes come in classes: **2xx** success, **3xx** look elsewhere, **4xx** the client did something wrong (don't retry unchanged), **5xx** the server failed (a retry might work).

| Code | Meaning |
|---|---|
| `200 OK` | Here's what you asked for |
| `201 Created` | A new resource exists now |
| `204 No Content` | Done; nothing to send back |
| `400 Bad Request` | The request is malformed or invalid |
| `404 Not Found` | No such resource |
| `405 Method Not Allowed` | The resource exists but doesn't support that method |
| `409 Conflict` | It clashes with the current state (a duplicate, a stale version) |
| `429 Too Many Requests` | Slow down (lesson 19) |
| `500` / `503` | The server broke / is overloaded or down |

## REST: resources and uniform methods

**REST** (representational state transfer) organizes an API around **resources**, the nouns of your domain, each identified by a URL: `/books`, `/books/8`, `/authors/1/books`. A small, fixed set of **methods** acts on any resource:

| Method | Meaning | Safe? | Idempotent? |
|---|---|---|---|
| `GET` | Read | Yes | Yes |
| `PUT` | Create or replace at this URL | No | Yes |
| `DELETE` | Remove | No | Yes |
| `PATCH` | Partially update | No | Not necessarily |
| `POST` | Create in a collection, or do an action | No | No |

- **Safe** means no side effects: anyone (a crawler, a cache, a prefetching browser) can call it freely.
- **Idempotent** means doing it twice has the same *effect* as doing it once. Deleting book 8 twice leaves book 8 deleted, even though the second call answers `404`. Idempotency matters because of timeouts: if a request times out, you don't know whether it ran, and only an idempotent request is safe to retry blindly.

`POST` isn't idempotent: retry a timed-out "create order" and you might get two orders. The standard fix is an **idempotency key**. The client generates a unique key per logical operation and sends it as a header. The server remembers the response it sent for each key and replays it for a retry instead of acting twice. Stripe's API works this way.

### Pagination

Never return an unbounded list. Two common schemes:

- **Offset**: `?offset=40&limit=20`. Simple, but slow for deep pages (the database still walks past the first 40), and rows shift when items are added or deleted mid-scroll.
- **Cursor**: `?after=137&limit=20`, where the cursor is the last item the client saw. The server answers "items after 137" with an index seek, and inserts elsewhere don't shift the page. The response includes the cursor for the next page, or nothing when there isn't one.

### Why REST dominates public APIs

Its uniformity is the point. Every HTTP client, proxy, and CDN understands `GET` is safe and cacheable, and `curl` is a debugger. The costs: a client that needs a book, its author, and their other books makes several round trips (**under-fetching**), and each response carries every field whether or not the client wants it (**over-fetching**).

## RPC: calling functions over the network

A **remote procedure call** makes a request look like a function call: `books.GetBook({id: 8})`. You define an interface, and the framework generates client and server code.

**gRPC**, Google's framework, is the most common today. You describe the service in a **Protocol Buffers** interface definition:

```protobuf
service Books {
  rpc GetBook (GetBookRequest) returns (Book);
  rpc ListBooks (ListBooksRequest) returns (stream Book);
}

message Book {
  int64 id = 1;
  string title = 2;
  int32 year = 3;
  int64 author_id = 4;
}
```

- **Compact binary encoding**: field numbers instead of names, so messages are much smaller and faster to parse than JSON (lesson 14 explains how this survives schema changes).
- **Generated, typed clients** in a dozen languages.
- **HTTP/2** underneath: many calls share one connection, and calls can **stream** many messages in either direction.
- **Deadlines**: every call carries a time budget that propagates to the calls it makes.
- **Status codes** of its own: `NOT_FOUND`, `INVALID_ARGUMENT`, `UNAVAILABLE`, `DEADLINE_EXCEEDED`, …

**JSON-RPC** is the minimal version of the same idea: a JSON body naming a method and its params, and a reply with either a `result` or an `error` with a numeric code.

```json
{"jsonrpc": "2.0", "method": "getBook", "params": {"id": 8}, "id": 1}
{"jsonrpc": "2.0", "id": 1, "result": {"id": 8, "title": "Kindred"}}
{"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "no method 'getBok'"}}
```

The trap with any RPC is believing the illusion. A remote call can time out with no way to know whether it ran, it's thousands of times slower than a local call, and its latency varies wildly. RPC is at its best *inside* an organization, between services you control on both sides.

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

## Your task

`solution.py` gives you a `Store` with a handful of methods, each counting as one database query in `store.calls`. Expose it three ways. `new_book_error(store, fields)` validates a new book's fields for you (title, author, optional year) and returns an error message, or `None`.

### 1. REST: `RestApi(store).handle(method, path, body=None, headers=None)` → `(status, body)`

| Request | Success | Failure |
|---|---|---|
| `GET /books/{id}` | `200`, the book | `404` |
| `GET /books?limit=&after=` | `200`, `{"books": [...], "next": cursor}` | `400` if `limit` isn't 1 to 100, or a value isn't an integer |
| `POST /books` | `201`, the new book | `400` if `new_book_error` reports a problem |
| `DELETE /books/{id}` | `204`, `None` | `404` |

- `limit` defaults to 10 and `after` to 0. `next` is the id of the page's last book when more books follow it, and `None` otherwise. Hint: ask the store for one more book than the limit.
- A `POST` with an `Idempotency-Key` header that you've already succeeded with returns the same response again without creating anything.
- A method a path doesn't support answers `405`. A path that doesn't exist answers `404`. Failures return a body like `{"error": "..."}`.

`urllib.parse` splits a path from its query: `urlsplit(path).path`, `parse_qs(urlsplit(path).query)`.

### 2. RPC: `RpcApi(store).call(request)` → reply

Requests look like `{"jsonrpc": "2.0", "method": "getBook", "params": {"id": 2}, "id": 7}`. Reply with `{"jsonrpc": "2.0", "id": <the request's id>, "result": ...}` or `..., "error": {"code": ..., "message": ...}}`.

- `getBook {id}`: the book, or error `NOT_FOUND` (−32004).
- `addBook {title, author_id, year?}`: the new book.
- `booksByAuthor {author_id}`: that author's books in id order (maybe none).
- An unknown method is `METHOD_NOT_FOUND` (−32601). Missing or invalid params are `INVALID_PARAMS` (−32602).

### 3. GraphQL: `GraphQLApi(store).execute(query)`

The parser is done: `parse(query)` returns a list of `Field(name, args, fields)`, where `fields` is the nested selection (empty for a scalar). `execute` already calls your two functions and turns a `GraphQLError` into `{"errors": [{"message": ...}]}`.

- `validate(type_name, fields)`: walk the selection against `SCHEMA` and raise `GraphQLError` for a field the type doesn't have, an object field (like `author`) with no subfields, or a scalar (like `title`) with subfields. Put the field's name in the message. This runs before any data is loaded.
- `resolve_query(fields)`: return `{"book": ...}` for `book(id:)` (or `None` if it doesn't exist) and `{"books": [...]}` for `books(limit:)` (all of them without a limit). Include exactly the requested fields, in the requested order.
- **No N+1**: a list of books with `author { ... }` takes two store calls in total, using `store.get_authors(ids)`. Without `author`, don't load authors at all.

Try all three in the **Scratchpad** against `SAMPLE`, and compare how many calls each takes to show a page of books with their authors' names.

## Key terms

| Term | Meaning |
|---|---|
| Resource | A thing with a URL that REST methods act on |
| Safe method | Has no side effects (`GET`) |
| Idempotent | Doing it twice has the same effect as once |
| Idempotency key | A client-chosen id that lets the server recognize a retry |
| Cursor pagination | Asking for items after the last one you saw |
| Over- / under-fetching | Getting fields you don't need / needing extra requests for ones you do |
| IDL | Interface definition language, such as a `.proto` file |
| Schema (GraphQL) | The typed description of every queryable field |
| Resolver | The code that fetches one field's value |
| N+1 problem | One query for a list plus one per item; fixed by batching |

Next, the systems underneath most of those APIs: databases.
