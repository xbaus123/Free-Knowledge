# A VLSM Planner in Python

*Chapter 5 · Subnetting in Practice.*

In chapter 4 you wrote a subnet calculator for one address at a time. Now build the tool you'd actually use to **plan** a network: give it a block and a list of groups, and it hands back a VLSM plan, largest first.

`ip_to_int`, `int_to_ip`, and `mask(prefix)` are already written for you at the top of the file.

## The one new trick: rounding up to a block boundary

Every block must start on a multiple of its own size. If the next free address is `nxt` and the block is `size` addresses, the first valid start at or after `nxt` is:

```python
start = (nxt + size - 1) // size * size
```

For example, after a /30 ending at .211, the next free address is .212. A /28 (size 16) can't start there: it rounds up to .224. That's also why VLSM goes **largest first**: big blocks placed first never need rounding, so nothing is wasted.

## Your task

- `hosts_to_prefix(hosts)`: the smallest subnet for that many hosts (50 → 26, 2 → 30). `ValueError` for fewer than 1.
- `parse_cidr(cidr)`: `"10.1.1.64/26"` → `(integer, 26)`. `ValueError` if the prefix is bad or the address isn't a network address (`"10.1.1.8/28"` has host bits set).
- `subnet_info(cidr)`: a dict with the network, broadcast, mask, gateway (first usable), last host, and host count.
- `split(cidr, new_prefix)`: fixed-length subnetting. Use every subnet, subnet zero included.
- `vlsm(cidr, needs)`: `needs` is a list of `(name, hosts)`. Sort by hosts, most first (Python's `sorted` is stable, so ties keep their order), place each block at the next aligned address, and raise `ValueError` if something doesn't fit.

The tests use the examples from this chapter's readings and drills, so you can check your work against them.

Use **Run** to try things out, and **Submit** to run the tests.
