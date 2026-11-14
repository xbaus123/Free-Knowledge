# HTTP Methods

*Chapter 9 · Upper Layers.*

The **method** is the verb of the request: what the client wants done to the resource named by the target. HTTP has nine standard methods.

| Method | What it does |
|---|---|
| **GET** | Request a representation of a resource: "send me this page" |
| **HEAD** | Like GET, but **only the headers** (metadata), no body. Used for caching: "has this changed?" |
| **POST** | **Submit** an entry to a resource: a form, a comment, an order |
| **PUT** | **Upload** data to a resource, creating it or **replacing it completely** |
| **PATCH** | Apply **partial** modifications to a resource |
| **DELETE** | **Remove** a resource |
| **OPTIONS** | Ask what communication options are available, such as which methods the server allows |
| **TRACE** | Echo back what the server received, for **troubleshooting** |
| **CONNECT** | Ask a **proxy** to open a tunnel to another server, used for HTTPS through a proxy |

## PUT vs PATCH vs POST

Say a user profile lives at `/users/42`:

- `PUT /users/42` with a whole profile **replaces** it. Fields you leave out are gone.
- `PATCH /users/42` with `{"email": "new@example.com"}` changes **just the email**.
- `POST /users` with a new profile **creates** a new user, and the server picks its address (say `/users/43`).

## Safe and idempotent

Two properties tell browsers, caches, and proxies what's OK to do automatically:

- **Safe**: the method only **reads**, it doesn't change anything. GET, HEAD, OPTIONS, and TRACE are safe.
- **Idempotent**: sending it **twice has the same effect as once**. All the safe methods are idempotent, and so are **PUT** and **DELETE**: replacing a profile twice with the same data, or deleting it twice, leaves the same result.
- **POST** is **neither**. Submitting an order twice can place two orders, which is why a browser warns you before resending a form.

## A security note

**TRACE** can echo back headers like cookies, so most servers **disable** it. And servers should only allow the methods they need: a public web server rarely needs PUT or DELETE turned on.

Next, a check on the methods.
