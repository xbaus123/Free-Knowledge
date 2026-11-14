# Project: Plan Your Site

*Chapter 9 · Upper Layers.*

Chapters 5 to 8 gave your project network its subnets, routing, names, and mail. Now it's time to plan the **website** that runs on it. Every question below has to be answered **even if you host in the cloud**: the cloud runs the hardware, but the design decisions are still yours.

## The questions

**1. What's the layout of your site's pages?**
Sketch every page and how they link: home, product or service pages, an account area, checkout, admin. Mark which are **public** and which need a **login**.

**2. How will you handle requests?**
- Which pages are **static** (the same for everyone: served straight from disk or a CDN) and which are **dynamic** (built per user by application code)?
- What sits in front of the web servers? A **load balancer** or **reverse proxy** on 443 terminates TLS and spreads requests across servers.
- Which **HTTP methods** does each part allow? Public pages need GET and HEAD. Forms need POST. Turn off **TRACE**, and anything else you don't use.

**3. Will there be transactions?**
If people buy, book, or pay, map the flow: cart, checkout, payment, confirmation. Each step that changes something is a POST, so protect it against **double submission** (a second click shouldn't charge twice).

**4. How will you store data?**
A **database** server on an internal subnet, never directly reachable from the Internet: only the application servers can connect to it. Which tables? Users, products, orders?

**5. How will you store sensitive data?**
- **Passwords**: never stored as is. Store a slow, salted **hash** (bcrypt or Argon2).
- **Card numbers**: best not stored at all. Use a **payment processor**, so card details go straight to them and you keep only a token.
- Personal details: **encrypted** at rest and only ever sent over **HTTPS**.

**6. How will you keep track of transactions?**
Each order gets an ID, a status (`pending`, `paid`, `shipped`), and timestamps. Keep an **audit log** of who changed what and when. Database transactions (**COMMIT** and **ROLLBACK**) make sure an order is never half-saved.

**7. How will you manage backups?**
- The **3-2-1 rule**: **3** copies, on **2** kinds of media, **1** off-site.
- How often (nightly full, hourly incremental?) and how long you keep them.
- **Test a restore.** A backup nobody has restored is a hope, not a plan.

## A worked example

The chapter 5 office's shop, `shop.example.com`:

| Piece | Choice |
|---|---|
| Front | Load balancer in the DMZ on **443** only, port 80 just redirects (**301**) to HTTPS |
| Web and app | Two app servers on 192.168.20.0/24, so either can fail |
| Database | PostgreSQL on 192.168.30.10, port 5432 open **only** to the app servers |
| Sessions | Random session ID cookie, `Secure; HttpOnly; SameSite=Lax`, 30 minute idle timeout |
| Payments | A hosted payment processor. The shop stores a token and the last four digits |
| Backups | Nightly database dump, encrypted, copied off-site, kept 30 days, restore tested monthly |

Next, a check on planning your site.
