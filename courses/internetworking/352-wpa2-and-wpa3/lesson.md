# WPA2 and WPA3

*Chapter 11 · Wireless and IoT.*

Chapter 2 said encryption is the first line of defense on a wireless network. On Wi-Fi, that encryption comes from **WPA** (**Wi-Fi Protected Access**).

| Protocol | Year | Status |
|---|---|---|
| **WEP** | 1997 | Broken. Can be cracked in minutes. Never use it |
| **WPA** | 2003 | A stopgap while WPA2 was finished |
| **WPA2** | 2004 | AES encryption. Still very common |
| **WPA3** | 2018 | The current standard |

## WPA2: one shared key

**WPA2-Personal** uses a **pre-shared key (PSK)**: the Wi-Fi password, the same for everyone. After association, the client and WAP run a **4-way handshake** that proves both know the key and derives fresh session keys from it.

The weakness: an attacker who records one handshake can take it home and try password guesses **offline**, as fast as their hardware allows, without ever going near the network again. And anyone who knows the password and saw your handshake can decrypt your traffic.

## WPA3: SAE

WPA3 replaces the PSK exchange with **Simultaneous Authentication of Equals (SAE)**. "Equals" because neither side acts as client or server: both run the same steps.

1. **Hash-to-Element (H2E).** Both sides turn the password (and the SSID) into the **Password Element (PWE)**, a value the rest of the math is built on.
2. **Commit, both sides.** Each side picks secret random values, and sends a commit message built from them and the PWE.
3. **Confirm, both sides.** Each proves it arrived at the same shared secret. Neither ever sends the password, or anything a guess could be tested against.
4. **4-way handshake.** Starting from the fresh key SAE just made, both sides confirm the keys and install the session encryption keys.

What this buys you:

- **No offline guessing.** Every guess needs a live exchange with the WAP, which can notice and slow down repeated failures.
- **Forward secrecy.** Every session gets a fresh key. Even if the password leaks later, traffic recorded earlier stays encrypted.

## Key sizes

- **WPA3-Personal**: **AES-128**.
- **WPA3-Enterprise**, 192-bit mode: **AES-256**. AES-256 is widely used and considered secure for commercial transactions, which is why businesses, banks, and governments use the enterprise mode.

Older devices that only speak WPA2 can join a **transition mode** network that accepts both, but a WPA2 device gets only WPA2's protection.

Next, a check on WPA2 and WPA3.
