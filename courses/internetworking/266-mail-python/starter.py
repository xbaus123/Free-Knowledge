"""A mail toolkit: addresses, MX order, SMTP commands, replies, and Received: paths."""

import re


# ---------------------------------------------------------------------------
# Part 1: where does the mail go?


def mail_domain(address):
    """The domain a sender looks up the MX for, lowercased.

    mail_domain("bob@Example.COM") == "example.com"
    mail_domain("Alice Smith <alice@example.org>") == "example.org"
    If the address is in angle brackets, use only what's inside them.
    Raise ValueError if there's no @.
    """
    # TODO
    pass


def delivery_order(mx_records, domain):
    """The hosts a sender tries, in order.

    mx_records are MX values like "10 mail1.example.com.".
    - Lowest priority number first (compare as numbers: 5 before 10);
      equal priorities keep their order from the list.
    - No MX records at all: the implicit MX, [domain] (lowercased).
    - A null MX (a record whose host is "."): [] -- this domain takes no mail.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 2: talking SMTP


def dot_stuff(line):
    """A body line as it's sent after DATA: a leading "." gets doubled."""
    # TODO
    pass


def smtp_commands(helo, sender, recipients, body_lines):
    """Every line the client sends, in order:

    EHLO <helo>, MAIL FROM:<sender>, one RCPT TO:<r> per recipient, DATA,
    the body lines (dot-stuffed), a lone ".", then QUIT.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 3: reading the server's replies


def reply_action(line):
    """What the client does with a reply line, from its first digit:

    2xx -> "ok", 3xx -> "continue", 4xx -> "retry", 5xx -> "bounce".
    Raise ValueError if the line doesn't start with a three-digit code from 2xx to 5xx.
    """
    # TODO
    pass


def parse_reply(lines):
    """A whole (possibly multi-line) reply -> (code, [text of each line]).

    ["250-mx.example.com", "250-STARTTLS", "250 8BITMIME"]
        -> (250, ["mx.example.com", "STARTTLS", "8BITMIME"])
    Every line but the last has "-" after the code; the last has " " (or nothing).
    Raise ValueError if the reply is empty, the codes differ, a line before the
    last has no dash, or the last line has a dash (the reply isn't finished).
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 4: tracing a message


def hop_path(headers):
    """The hosts that received the message, first hop first.

    headers is a list of header lines, top to bottom. For each line starting
    with "Received:" (any case), take the host name after the word "by".
    Remember: the TOP Received: header is the LAST hop.
    """
    # TODO
    pass


if __name__ == "__main__":
    print(mail_domain("Bob <bob@Example.com>"))                          # example.com
    print(delivery_order(["20 b.example.com.", "10 a.example.com."], "example.com"))
    # ['a.example.com.', 'b.example.com.']
    print(smtp_commands("mail.example.org", "alice@example.org", ["bob@example.com"], ["Hi", ".net rocks"]))
    # ['EHLO mail.example.org', 'MAIL FROM:<alice@example.org>', 'RCPT TO:<bob@example.com>',
    #  'DATA', 'Hi', '..net rocks', '.', 'QUIT']
    print(reply_action("451 4.7.1 Try again later"))                     # retry
    print(parse_reply(["250-mx.example.com", "250 STARTTLS"]))           # (250, ['mx.example.com', 'STARTTLS'])
