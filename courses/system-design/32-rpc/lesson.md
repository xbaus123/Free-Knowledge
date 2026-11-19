# RPC: Calling Functions over the Network

*Chapter 1 · Foundations.*

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

- **Compact binary encoding**: field numbers instead of names, so messages are much smaller and faster to parse than JSON (chapter 4 explains how this survives schema changes).
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

Next, a short check on what you just read.
