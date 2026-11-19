# Where to Terminate TLS

*Chapter 2 · The Front Door.*

## Where to terminate TLS

**Terminating** TLS means decrypting it. Where you do it is an architecture decision:

| Option | How | Gains | Costs |
|---|---|---|---|
| **Terminate at the edge** | The load balancer or gateway decrypts and forwards plain HTTP inside | Certificates in one place; L7 routing, caching, and inspection; servers skip crypto | Traffic inside the network is plaintext: anyone inside can read it |
| **Re-encrypt** (TLS bridging) | The edge decrypts, inspects, and opens a new TLS connection to the backend | L7 features *and* encryption inside | Two handshakes; certificates on every backend |
| **Passthrough** | An L4 balancer forwards encrypted bytes; the backend terminates | True end-to-end encryption; the edge never sees plaintext | No L7 routing, header inspection, or caching at the edge |

Terminating at the edge was the classic setup, on the theory that the internal network is trusted. That theory has failed repeatedly: one compromised machine inside can read everything. The modern stance is **zero trust**: no network location is trusted by default, and every connection is authenticated and encrypted. Inside the data center, that usually means **mutual TLS (mTLS)**, where the *client* also presents a certificate, so both sides know who the other is. Managing certificates for thousands of service instances by hand is impossible, so a service mesh (chapter 9) issues short-lived certificates to every instance automatically, often as **SPIFFE** identities like `spiffe://example.com/orders`.

At the edge, certificates come from a public CA. Automate their issuance and renewal with the **ACME** protocol (as Let's Encrypt does), because an expired certificate is one of the most common self-inflicted outages. One IP address can serve many host names, because the client names the host it wants in the handshake (**SNI**, server name indication), and the server picks the matching certificate.

Next, a short check on what you just read.
