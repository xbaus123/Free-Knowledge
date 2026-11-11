# MAC Addresses in Python

*Chapter 3 · The Data Link Layer.*

You've read MAC addresses by eye. Now write the code that does it: the same checks a packet sniffer or a network inventory tool runs on every address it sees.

## Formats

The same 48 bits get written several ways, and `arp -a` on a Mac even drops leading zeros:

| Written as | Where you'll see it |
|---|---|
| `01:00:5e:00:00:fb` | macOS, Linux |
| `01-00-5E-00-00-FB` | Windows |
| `0100.5e00.00fb` | Cisco |
| `01005e0000fb` | Bare hex, in logs and databases |
| `1:0:5e:0:0:fb` | macOS `arp -a` |

## The bits

Turn the first octet into a number with `int(octet, 16)`, then test single bits with `&`:

```
 first_byte & 1   → 1 means multicast (the I/G bit)
 first_byte & 2   → 2 means locally administered (the U/L bit)
```

## Your task

Implement these functions in the editor:

- `normalize_mac(text)`: return the address as six **two-digit lowercase** hex pairs joined by colons, from any of the formats above. Ignore spaces around it. Raise `ValueError` for anything that isn't a MAC address: the wrong number of octets, an octet with more than two digits (or none), or a character that isn't hex.
- `oui(mac)`: the first three octets, normalized, such as `"3c:bd:c5"`.
- `is_broadcast(mac)`: `True` only for `ff:ff:ff:ff:ff:ff`.
- `is_multicast(mac)`: `True` when bit 0 of the first byte is 1. Broadcast counts as multicast.
- `is_locally_administered(mac)`: `True` when bit 1 of the first byte is 1.
- `describe(mac, vendors=VENDORS)`: return `"broadcast"`, `"multicast"`, or `"locally administered"`, checked in that order. Otherwise look the OUI up in `vendors` and return the vendor's name, or `"unknown"` if it isn't there.

Every function should accept a MAC address in any format, so build the others on top of `normalize_mac`.

Use **Run** to try things out, and **Submit** to run the tests.
