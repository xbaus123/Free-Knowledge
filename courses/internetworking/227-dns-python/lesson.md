# A Resolver in Python

*Chapter 7 · DNS.*

Time to build the pieces of a resolver this chapter described. Every function uses an example from the readings or drills, so you can check your answers against them.

`normalize(name)` and the `QTYPES` table are already written for you at the top of the file. `normalize` lowercases a name and makes sure it ends in the root's dot, so `WWW.Example.com` and `www.example.com.` compare equal.

## Part 1: names on the wire

`encode_name(name)` turns a name into the bytes DNS actually sends: each label as **one length byte, then the label**, ending with a **zero byte** for the root.

```python
encode_name("www.example.com")  # b"\x03www\x07example\x03com\x00"
```

A label can be at most **63** bytes; raise `ValueError` for a longer one.

`build_query(query_id, name, qtype)` builds a whole query message: the 12-byte **header**, then the **question**. Python's `struct.pack("!HHHHHH", ...)` packs six 16-bit numbers in network byte order. The header fields are the ID, the flags (`0x0100`: just **rd**, recursion desired), and four counts: one question, zero answers, zero authority, zero additional. The question is the encoded name, then the QTYPE number and QCLASS 1 (IN), as `struct.pack("!HH", ...)`.

## Part 2: reverse names

`reverse_name("192.0.2.10")` returns `"10.2.0.192.in-addr.arpa."`: octets reversed, as in the MX and PTR lesson.

## Part 3: where to start

`closest_zone(name, zones)` is step 2 of the resolver algorithm: of the zones you know servers for, pick the **closest ancestor** of the name. It's longest prefix match from chapter 6, but on **labels from the right**. Careful: `notexample.com` is **not** inside `example.com`, even though the text ends the same way.

## Part 4: answering from records

- `resolve(records, name, rtype)`: return the values of every matching record. If there are none but the name has a **CNAME**, follow it, as the resolver algorithm does. Give up (return `[]`) after 8 aliases, so a CNAME loop can't hang you.
- `mail_hosts(records, domain)`: the MX hosts in the order a sender tries them, **lowest priority number first**.

Use **Run** to try things out, and **Submit** to run the tests.
