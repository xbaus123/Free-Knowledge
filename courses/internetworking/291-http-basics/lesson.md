# HTTP: The Web's Protocol

*Chapter 9 · Upper Layers.*

We've already covered two big application-layer protocols, DNS and mail. The one left is the one you use most: **HTTP**, the **HyperText Transfer Protocol**, and its secure form, **HTTPS**.

## Requests and responses

HTTP is **client-server** and **request-response**. A client (usually a browser) opens a TCP connection to a server, sends a **request**, and gets back a **response**.

| | Port |
|---|---|
| **HTTP** | TCP **80** |
| **HTTPS** (HTTP inside TLS) | TCP **443** |

Visiting `http://www.example.com/menu.html` means: look up `www.example.com` in DNS, connect to that address on port 80, and ask for `/menu.html`.

## What a request looks like

HTTP/1.1 is **plain text**, like SMTP. A request is a **request line**, then **headers**, then a **blank line**, then an optional **body**:

```
GET /menu.html HTTP/1.1
Host: www.example.com
User-Agent: Firefox/140.0
Accept: text/html

```

- The request line has three parts: the **method** (`GET`), the **target** (`/menu.html`), and the **version**.
- **Host** is required in HTTP/1.1. It's how one server at one IP address can host many websites.
- The blank line marks the end of the headers.

## What a response looks like

```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 1834

<!doctype html> ...
```

A **status line** (version, **status code**, reason), headers, a blank line, and the **body**: here, the page itself.

## Stateless

HTTP is **stateless**: each request stands on its own, and the server doesn't remember the last one. That keeps servers simple, but it means sessions like a login have to be **built on top**. You'll see how with cookies later in the chapter.

Next, a check on the basics.
