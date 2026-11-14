# Status Codes and Headers

*Chapter 9 · Upper Layers.*

Every response starts with a **three-digit status code**. Like SMTP's replies in chapter 8, the **first digit** tells you the kind of answer.

| Class | Meaning | Common codes |
|---|---|---|
| **1xx** | Informational: keep going | **100** Continue, **101** Switching Protocols |
| **2xx** | **Success** | **200** OK, **201** Created, **204** No Content |
| **3xx** | **Redirection**: look somewhere else | **301** Moved Permanently, **302** Found, **304** Not Modified |
| **4xx** | **Client error**: the request was wrong | **400** Bad Request, **401** Unauthorized, **403** Forbidden, **404** Not Found, **405** Method Not Allowed |
| **5xx** | **Server error**: the request was fine, the server failed | **500** Internal Server Error, **502** Bad Gateway, **503** Service Unavailable |

A few worth telling apart:

- **401 vs 403.** 401 means "**who are you?**": log in and try again. 403 means "I know who you are, and **you're not allowed**."
- **301 vs 302.** 301 is a permanent move, so browsers and search engines remember the new address. 302 is temporary.
- **304 Not Modified** has no body. It tells a cache "your copy is still good", which saves sending the page again.
- **502 Bad Gateway** comes from a proxy or load balancer whose **backend** server didn't answer properly.

Careful with chapter 8: in **SMTP**, 4xx means "temporary, try again later". In **HTTP**, 4xx means "**your** mistake", and retrying the same request won't help.

## Headers worth knowing

| Header | Direction | Job |
|---|---|---|
| `Host` | Request | Which website |
| `Content-Type` | Both | What the body is: `text/html`, `application/json`, `image/png` |
| `Content-Length` | Both | Body size in bytes |
| `Location` | Response | Where to go, with a 3xx (or the new resource, with 201) |
| `Cache-Control` | Response | How long the response may be cached |
| `ETag` | Response | A version tag for the resource. Send it back in `If-None-Match` and you may get a 304 |
| `Set-Cookie` / `Cookie` | Response / Request | Session state, coming up shortly |

Next, a check on status codes and headers.
