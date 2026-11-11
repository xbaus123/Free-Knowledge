# Cyclic Redundancy Check

*Chapter 3 · The Data Link Layer.*

Parity misses any even number of flipped bits. The **cyclic redundancy check (CRC)** is a much more powerful error-detection code, and it's what Ethernet and 802.11 WiFi use in practice.

## The setup

- **D**: the **d** data bits. Treat them as one long binary number.
- **G**: the **generator**, a bit pattern of **r + 1** bits. It's fixed by the CRC standard, so sender and receiver both know it. Its first bit is always 1.
- **R**: the **r** CRC bits the sender computes and appends.

```
   ◀──── d data bits ────▶◀ r bits ▶
  ┌───────────────────────┬────────┐
  │           D           │   R    │   ← bits to send
  └───────────────────────┴────────┘
       <D,R> = D · 2^r  XOR  R
```

`D · 2^r` just means D shifted left by r places (r zeros on the end). XOR-ing R in fills those zeros with the CRC bits.

**The sender's job**: choose R so that the whole thing, `<D,R>`, divides **exactly** by G, using mod-2 arithmetic.
**The receiver's job**: divide what arrived by G. A remainder of zero means no error detected. **Any non-zero remainder means an error.**

## Mod-2 arithmetic

Mod-2 arithmetic has no carries and no borrows: **adding and subtracting are both XOR**. So long division works like ordinary long division, except each "subtract" is an XOR.

To find R: append r zeros to D, divide by G, and **R is the remainder**.

## A worked example

D = `101110`, G = `1001` (4 bits, so r = 3). Append three zeros and divide:

```
        1 0 1 0 1 1          ← quotient (not needed)
      ┌──────────────────
 1001 │ 1 0 1 1 1 0 0 0 0
        1 0 0 1              ← leading bit 1: XOR with G
        ───────
          0 1 0 1            ← drop the leading 0, bring down the next bit
          0 0 0 0            ← leading bit 0: XOR with 0000
          ───────
            1 0 1 0 0
            1 0 0 1
            ───────
              0 1 1 0 0
              0 0 0 0
              ───────
                1 1 0 0 0
                1 0 0 1
                ───────
                  1 0 1 0
                  1 0 0 1
                  ───────
                    0 1 1   ← remainder R
```

So R = `011`, and the sender transmits `101110 011`.

The receiver divides `101110011` by `1001` and gets remainder `000`: no error. If a bit flips in transit, say `101010011` arrives, the remainder is `100`, which isn't zero, so the frame is dropped.

## Why CRC is so good

- A CRC with r check bits detects **every burst error shorter than r + 1 bits**: any run of r or fewer damaged bits in a row.
- It also catches any odd number of flipped bits (with a well-chosen G), and longer bursts with probability of about 1 − 0.5^r.
- Ethernet's CRC-32 has r = 32, so a corrupted frame slipping through is roughly a one-in-four-billion event.
- It's fast in hardware: the division is just shifts and XORs, so a NIC computes it as the bits stream past.

Next, a check on CRC, including working one out yourself.
