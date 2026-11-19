# Authorization Models

*Chapter 2 · The Front Door.*

## Authorization models

Once you know *who*, you decide *what*. The models, from simplest to most expressive:

| Model | Rule shape | Good at | Example |
|---|---|---|---|
| **ACL** (access control list) | Each resource lists who may do what | Small numbers of shared objects | File permissions |
| **RBAC** (role-based) | Users have roles; roles grant permissions | Organizations with clear job functions | "support can refund orders" |
| **ABAC** (attribute-based) | Policies over attributes of user, resource, and context | Rules that depend on data | "managers can approve expenses under $5,000 in their own department, during business hours" |
| **ReBAC** (relationship-based) | Permissions follow a graph of relationships | Sharing and nesting | "you can edit a doc if you're an editor of its folder" |

**RBAC** is the common default. Permissions are strings like `orders:refund`. Roles bundle permissions, and roles can **inherit** from other roles, so `manager` gets everything `support` has and more. It's easy to audit (list who has which role), but it struggles when access depends on the specific object: "customers can read *their own* orders" isn't a role. Large systems such as Google's **Zanzibar** (behind Drive and YouTube sharing) and its open-source descendants like SpiceDB use **ReBAC**, storing billions of relationship tuples and answering "can user U do X on object O?" in milliseconds. Policy engines like **Open Policy Agent** let you write ABAC rules as code, separate from the services that enforce them.

### Where to enforce

- **At the gateway**: coarse checks. Is the token valid? Does this caller have `orders:read` at all? Rejecting bad requests at the edge protects every service behind it.
- **In the service**: fine-grained checks. Is order 7 *this user's* order? Only the service has the data to answer. Skipping this check is **broken object-level authorization** (also called IDOR), the most common API vulnerability in the OWASP API Security Top 10: change `/orders/7` to `/orders/8` and read a stranger's order.

The gateway passes the verified identity to services in headers, so it **must strip** any identity headers the client sent itself. Otherwise a client simply sends `X-User-Id: admin`. Services should accept those headers only from the gateway (enforced by mTLS or network policy), or verify the token again themselves.

Next, a short check on what you just read.
