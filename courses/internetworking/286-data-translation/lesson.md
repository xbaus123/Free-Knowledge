# Data Translation: Bytes Everyone Agrees On

*Chapter 9 · Upper Layers.*

A deeper look at the first job. Every format below is a way for two programs to agree on what a sequence of bytes **means**.

## Characters

| Encoding | Covers | Bytes per character |
|---|---|---|
| **ASCII** | English letters, digits, punctuation (128 characters) | 1 (only 7 bits used) |
| **EBCDIC** | IBM mainframes' own set | 1 |
| **UTF-8** | **Every** character in **Unicode**: every language, plus emoji | 1 to 4 |

**UTF-8** is the Web's standard. It was designed so that plain ASCII text is **already valid UTF-8**, byte for byte, which is why it took over. A web server says which encoding it used in a header like `Content-Type: text/html; charset=utf-8`. If the browser guesses wrong, you see garbage like `cafÃ©` instead of `café`.

## Numbers and byte order

The 16-bit number 1 can be stored as `00 01` (**big-endian**) or `01 00` (**little-endian**). Internet protocols agree on **big-endian**, called **network byte order**. Every port number and IP address in the headers you've studied is sent big-endian, and a little-endian PC converts before sending and after receiving.

## Structured data

Programs don't just send text, they send **records**: a user with a name, an age, and a list of orders. Turning a record into bytes is **serialization** (the same thing RPC called marshalling):

```json
{"name": "Alice", "age": 30, "orders": [1042, 1043]}
```

- **JSON**: text, easy to read, used by most web APIs.
- **XML**: text, older, wordier.
- **Protocol Buffers**: binary, compact, used by gRPC.

## Base64

Some channels only carry **text** safely. Chapter 8's mail was one: **MIME** attachments are sent in **Base64**, which turns every **3 bytes** of binary into **4** text characters (`A` to `Z`, `a` to `z`, `0` to `9`, `+`, `/`). It makes data about **33% bigger**, and it's **not encryption**: anyone can decode it.

Next, a check on data translation.
