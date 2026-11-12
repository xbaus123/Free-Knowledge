# IP Addresses in Python

*Chapter 4 · The Network Layer.*

Time to turn the last few lessons into code. You'll write the core of a subnet calculator, the same arithmetic routers and operating systems do millions of times a second.

## The trick: addresses are just numbers

An IPv4 address is a 32-bit integer, so treat it as one. `192.168.1.15` is

```
192 × 2²⁴ + 168 × 2¹⁶ + 1 × 2⁸ + 15  =  3232235791
```

Once you have integers, everything is bit operations:

- A mask with `p` ones: `(0xFFFFFFFF << (32 - p)) & 0xFFFFFFFF`. The `& 0xFFFFFFFF` keeps it to 32 bits, since Python integers don't overflow.
- Network address: `ip & mask`
- Broadcast address: `network | (~mask & 0xFFFFFFFF)`, every host bit set to 1
- The first octet: `ip >> 24`

Python's standard library has an `ipaddress` module that does all of this, but don't use it here: the point is to see how it works.

## Your task

Implement these in the editor:

- `ip_to_int(text)` and `int_to_ip(n)`: convert between dotted decimal and a 32-bit integer. `ip_to_int` raises `ValueError` for anything that isn't exactly four decimal octets from 0 to 255 (like `"10.0.0"`, `"1.2.3.256"`, or `"a.b.c.d"`).
- `address_class(ip)`: `"A"`, `"B"`, `"C"`, `"D"`, or `"E"`, from the first octet.
- `is_private(ip)`: is it in one of the three RFC 1918 ranges? `is_loopback(ip)`: is it on the 127 network?
- `prefix_to_mask(prefix)` and `mask_to_prefix(mask)`: convert `24` to `"255.255.255.0"` and back. `mask_to_prefix` raises `ValueError` for a mask whose 1s aren't all at the front.
- `network_address(ip, prefix)` and `broadcast_address(ip, prefix)`, returned as dotted decimal.
- `usable_hosts(prefix)`: 2ʰ − 2, except a /31 has 2 (a point-to-point link with no network or broadcast address, RFC 3021) and a /32 has 1.
- `same_subnet(a, b, prefix)`: the decision every host makes before sending.

Use **Run** to try things out, and **Submit** to run the tests.
