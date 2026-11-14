# HTTPS, Cookies, and Sessions

*Chapter 9 · Upper Layers.*

This reading ties the chapter together: HTTPS is the **presentation** layer's encryption under HTTP, and cookies are how HTTP builds **sessions** on a stateless protocol.

## HTTPS

**HTTPS** is HTTP carried inside **TLS**, on port **443**:

1. The browser connects to port 443 and starts a **TLS handshake**.
2. The server sends its **certificate**: its name and public key, signed by a **certificate authority (CA)** the browser trusts. If the name on the certificate doesn't match the site, the browser shows a warning.
3. The two sides agree on a symmetric key (asymmetric crypto, as in the encryption reading).
4. Ordinary HTTP requests and responses now flow, **encrypted**.

What HTTPS gives you: **confidentiality** (nobody on the path can read it), **integrity** (nobody can change it unnoticed), and **authentication** (you're really talking to that site). What an eavesdropper still sees: the server's IP address and, usually, the site's name. They don't see the page, the path, or your cookies.

## Cookies: sessions on a stateless protocol

When you log in, the server creates a **session** with a random **session ID** and sends it in a header:

```
HTTP/1.1 302 Found
Location: /account
Set-Cookie: session=8f3a9c2e7b; Secure; HttpOnly; SameSite=Lax
```

From then on the browser sends it back with **every** request to that site:

```
GET /account HTTP/1.1
Host: shop.example.com
Cookie: session=8f3a9c2e7b
```

The server looks up `8f3a9c2e7b`, finds Alice's session, and knows who's asking. Log out, and the server deletes the session.

| Cookie attribute | Effect |
|---|---|
| **Secure** | Only sent over HTTPS |
| **HttpOnly** | JavaScript on the page can't read it, which limits theft by injected scripts |
| **SameSite** | Not sent on most requests from other sites, which blocks cross-site request forgery |
| **Expires** / **Max-Age** | When the cookie goes away. Without one, it lasts until the browser closes |

A session ID is as good as a password while it lasts: anyone who steals it **is** you. That's why it should only ever travel over HTTPS.

## HTTP versions

**HTTP/1.1** is text and handles one request at a time per connection. **HTTP/2** is binary and **multiplexes** many requests on one connection. **HTTP/3** runs over **QUIC**, on **UDP**, to avoid TCP's head-of-line blocking. The methods, status codes, and headers are the same in all three.

Next, a check on HTTPS and cookies.
