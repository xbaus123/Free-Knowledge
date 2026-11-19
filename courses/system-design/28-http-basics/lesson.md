# APIs and HTTP

*Chapter 1 · Foundations.*

An **API** is a contract: what a caller may ask for, how to ask, and what comes back. Inside one program, that contract is a function signature. Between programs it's a **protocol** over the network, and the network brings everything from earlier in this chapter: latency, lost requests, retries, and two sides that upgrade at different times.

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
| `429 Too Many Requests` | Slow down (chapter 6) |
| `500` / `503` | The server broke / is overloaded or down |

Next, a short check on what you just read.
