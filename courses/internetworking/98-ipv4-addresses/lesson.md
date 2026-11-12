# IPv4 Addresses

*Chapter 4 · The Network Layer.*

An IPv4 address is **32 bits**. Nobody wants to read 32 ones and zeros, so we write it as four **octets** (bytes), each in decimal, separated by dots: **dotted decimal**.

```
 11000000 . 10101000 . 00000001 . 00001111
    192   .   168    .    1     .    15
```

Each octet is 8 bits, so it ranges from **0 to 255**. `192.168.1.256` is not an address.

## Converting an octet

Each bit in an octet has a place value:

```
 128  64  32  16   8   4   2   1
  1    1   0   0   0   0   0   0    = 128 + 64           = 192
  1    0   1   0   1   0   0   0    = 128 + 32 + 8       = 168
  0    0   0   0   1   1   1   1    = 8 + 4 + 2 + 1      = 15
```

To go the other way, subtract the biggest place value that fits, and repeat: 200 = 128 + 64 + 8 → `11001000`.

## Network part and host part

An IP address isn't just a serial number. It has two parts:

- The **network ID** (netid): which network the host is on. Every host on the same network shares it.
- The **host ID** (hostid): which host on that network.

That split is what makes routing possible. A router doesn't need to know about every one of billions of hosts; it only needs to know how to reach each **network**. Exactly where the split falls is the subject of the next few lessons: first the original fixed **classes**, then the flexible **subnet mask**.

## Static or dynamic

A host gets its address in one of two ways:

- **Static**: someone types it in, and it doesn't change. Servers, routers, and printers usually have static addresses, so everyone else can find them. On macOS and older Linux you use `ifconfig`, on modern Linux `ip addr`, and on Windows the network settings (or `netsh`).
- **Dynamic**: the host asks a **DHCP** server for one when it joins the network. Laptops and phones almost always work this way. More on DHCP later in the chapter.

To see your own address: `ipconfig` on Windows, `ifconfig` on macOS, `ip addr` on Linux.

Next, a check on reading and converting addresses.
