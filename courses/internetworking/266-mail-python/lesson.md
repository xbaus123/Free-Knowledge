# A Mail Toolkit in Python

*Chapter 8 · Mail.*

Time to build the pieces a sending server needs. Every function uses an example from the readings or drills, so you can check your answers against them.

## Part 1: where does the mail go?

- `mail_domain(address)`: the domain after the `@`, lowercased. Addresses can come with a display name, like a `From:` header: `Alice Smith <alice@example.org>`. When there are angle brackets, only what's inside them counts. Raise `ValueError` if there's no `@`.
- `delivery_order(mx_records, domain)`: the hosts a sender tries, in order. MX values look like `"10 mail1.example.com."`. **Lowest number first**, comparing as numbers, and equal priorities keep their order. Two special cases from the reading:
  - **No MX records**: the implicit MX, `[domain]`.
  - **A null MX** (`"0 ."`): `[]`, because the domain takes no mail.

## Part 2: talking SMTP

- `dot_stuff(line)`: a body line as it's sent after `DATA`. A line that **starts** with a dot gets a second one.
- `smtp_commands(helo, sender, recipients, body_lines)`: every line the client sends, as in the Talking SMTP reading: `EHLO`, `MAIL FROM:<...>`, one `RCPT TO:<...>` per recipient, `DATA`, the dot-stuffed body, the lone `.`, and `QUIT`.

```python
smtp_commands("mail.example.org", "alice@example.org", ["bob@example.com"], ["Hi"])
# ['EHLO mail.example.org', 'MAIL FROM:<alice@example.org>', 'RCPT TO:<bob@example.com>',
#  'DATA', 'Hi', '.', 'QUIT']
```

## Part 3: reading replies

- `reply_action(line)`: what the client does, from the **first digit**: 2 is `"ok"`, 3 is `"continue"`, 4 is `"retry"`, 5 is `"bounce"`. Raise `ValueError` for anything that doesn't start with a three-digit code from 2xx to 5xx.
- `parse_reply(lines)`: a whole reply as `(code, texts)`. Every line but the last has a **dash** after the code, and the last has a **space** (or nothing at all). Raise `ValueError` if the reply is empty, the codes don't match, it ends early, or it isn't finished.

## Part 4: tracing a message

`hop_path(headers)`: the hosts named after **`by`** in each `Received:` header, **first hop first**. The top `Received:` header is the **last** hop, so you'll need to reverse them.

Use **Run** to try things out, and **Submit** to run the tests.
