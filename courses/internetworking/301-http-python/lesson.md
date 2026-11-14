# An HTTP Toolkit in Python

*Chapter 9 · Upper Layers.*

Time to build the pieces a browser or web server needs to read and write HTTP. Every function uses an example from the readings or drills, so you can check your answers against them.

## Part 1: requests

- `parse_request_line(line)`: split `GET /menu.html HTTP/1.1` into `("GET", "/menu.html", "HTTP/1.1")`. Raise `ValueError` unless there are exactly **three** parts, the method is one of the **nine** from the methods reading, and the version starts with `HTTP/`.
- `build_request(method, host, path="/", headers=None, body="")`: the whole request as text. Lines end in **CRLF** (`\r\n`), as on the wire:

```python
build_request("GET", "www.example.com", "/menu.html")
# 'GET /menu.html HTTP/1.1\r\nHost: www.example.com\r\n\r\n'
```

The **Host** header always comes first. Then the extra headers, in order. If there's a body, add `Content-Length`, counting **bytes** in UTF-8, not characters (`é` is two bytes). Then the blank line, then the body.

## Part 2: responses

- `parse_status_line(line)`: `HTTP/1.1 503 Service Unavailable` becomes `("HTTP/1.1", 503, "Service Unavailable")`. The reason can have spaces, or be missing. Raise `ValueError` for a bad version or a code that isn't three digits from 100 to 599.
- `status_class(code)`: `"informational"`, `"success"`, `"redirection"`, `"client error"`, or `"server error"`, from the first digit.

## Part 3: methods

`is_safe(method)` and `is_idempotent(method)`, from the table in the methods reading. Ignore case.

## Part 4: headers and cookies

- `parse_headers(lines)`: a dict of **lowercase** names to trimmed values. Split at the **first** colon only, since values like `https://example.com:8443/` have colons too. A repeated header's values are joined with `", "`.
- `parse_cookies(header)`: the value of a `Cookie:` header as a dict, as in the HTTPS and cookies reading.

Use **Run** to try things out, and **Submit** to run the tests.
