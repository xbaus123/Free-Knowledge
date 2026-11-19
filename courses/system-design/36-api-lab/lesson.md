# API Paradigms: REST, RPC, and GraphQL

*Chapter 1 · Foundations.*

Expose one small book store three ways, using what you learned about REST, RPC, and GraphQL.

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

Next, you'll meet the systems underneath most of those APIs: databases.
