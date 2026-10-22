# Encoding and Evolution

*Based on* Designing Data-Intensive Applications*, Chapter 4.*

Applications change, and they rarely change everywhere at once. Servers get a **rolling upgrade**, one machine at a time. Mobile users update their apps whenever they feel like it. Data written years ago is still in the database. So old and new code, and old and new data, must coexist:

- **Backward compatibility**: newer code can read data written by older code.
- **Forward compatibility**: older code can read data written by newer code. This is harder, because old code must ignore things it has never seen.

## Encoding formats

In memory, data lives in objects and pointers. To store it or send it, you **encode** (serialize) it into bytes.

- **Language-specific formats** (Java serialization, Python `pickle`) tie you to one language, are often insecure (decoding can run arbitrary code), and handle versioning poorly. Avoid them for anything that leaves the process.
- **JSON, XML, CSV** are readable and universal but ambiguous. JSON doesn't distinguish integers from floats, and numbers above 2⁵³ lose precision in JavaScript. Binary data needs Base64, which makes it a third bigger. Field names repeat in every record.
- **Binary schema-based formats** (Protocol Buffers, Thrift, Avro) are compact, fast, and come with clear evolution rules.

## Protocol Buffers and Thrift

You write a schema, and every field gets a **tag number**:

```protobuf
message Person {
  string user_name       = 1;
  int64  favorite_number = 2;
  repeated string interests = 3;
}
```

The encoded bytes contain **tag numbers, not field names**, followed by the value. So:

- You can **rename** a field freely; the tag is what matters on the wire.
- **Add** a field with a new tag. Old code skips tags it doesn't know (forward compatibility). New code reading old data finds the field missing and uses a default, so new fields must be optional (backward compatibility).
- **Remove** only optional fields, and **never reuse** a removed tag. Reserve it. Otherwise old data or old code will interpret the bytes as something else.
- **Changing a type** is risky. Widening int32 to int64 can work for new readers, but old 32-bit readers truncate big values.

## Avro

Avro has no tag numbers. The encoding is just values concatenated in schema order, so it's even more compact. To decode it, you must know the **exact schema it was written with** (the *writer's schema*). The reader resolves differences against its own *reader's schema* by matching fields **by name**:

- Fields in the writer's schema but not the reader's are ignored.
- Fields in the reader's schema but not the writer's are filled with the reader's **default**. To stay compatible, you may only add or remove fields that have a default.
- Renaming needs an **alias** in the reader's schema.

How does the reader get the writer's schema? Large files put it once in the header. Databases record a schema version with each record. Network protocols negotiate it when connecting. Kafka setups often use a **schema registry**: each message carries a schema id, and producers can't publish an incompatible schema. Because Avro needs no hand-assigned tags, it's friendly to **generated schemas**, such as dumping a whole relational database.

## Modes of dataflow

- **Through databases**: the writer encodes and a later reader decodes. *Data outlives code*: rows written five years ago are still there. Watch out: old code that reads a row, updates it, and writes it back can silently **drop fields** added by newer code.
- **Through services (REST/RPC)**: servers usually update before clients, so requests need backward compatibility and responses need forward compatibility. Public APIs may have to keep old versions around for a long time.
- **Through message brokers**: senders and receivers evolve independently, so encode messages with a format that supports both directions.

Answer the questions on the right.
