"""A mail toolkit: addresses, MX order, SMTP commands, replies, and Received: paths."""

import re


def mail_domain(address):
    if "@" not in address:
        raise ValueError("no @ in address: " + address)
    if "<" in address and ">" in address:
        address = address[address.index("<") + 1:address.rindex(">")]
    domain = address.strip().rsplit("@", 1)[1].strip().lower()
    if not domain:
        raise ValueError("no domain in address")
    return domain


def delivery_order(mx_records, domain):
    if not mx_records:
        return [domain.lower()]
    parsed = []
    for record in mx_records:
        priority, host = record.split()
        parsed.append((int(priority), host))
    if any(host == "." for _, host in parsed):
        return []
    parsed.sort(key=lambda p: p[0])
    return [host for _, host in parsed]


def dot_stuff(line):
    return "." + line if line.startswith(".") else line


def smtp_commands(helo, sender, recipients, body_lines):
    commands = ["EHLO " + helo, "MAIL FROM:<" + sender + ">"]
    commands += ["RCPT TO:<" + r + ">" for r in recipients]
    commands.append("DATA")
    commands += [dot_stuff(line) for line in body_lines]
    commands += [".", "QUIT"]
    return commands


ACTIONS = {"2": "ok", "3": "continue", "4": "retry", "5": "bounce"}


def reply_action(line):
    code = line[:3]
    if len(code) != 3 or not code.isdigit() or code[0] not in ACTIONS:
        raise ValueError("not an SMTP reply: " + line)
    return ACTIONS[code[0]]


def parse_reply(lines):
    code = None
    texts = []
    for i, line in enumerate(lines):
        this = int(line[:3])
        if code is not None and this != code:
            raise ValueError("codes don't match")
        code = this
        sep = line[3:4]
        last = i == len(lines) - 1
        if last and sep not in (" ", ""):
            raise ValueError("reply isn't finished")
        if not last and sep != "-":
            raise ValueError("reply ended early")
        texts.append(line[4:])
    if code is None:
        raise ValueError("empty reply")
    return code, texts


def hop_path(headers):
    hosts = []
    for line in headers:
        if not line.lower().startswith("received:"):
            continue
        match = re.search(r"\bby\s+(\S+)", line)
        if match:
            hosts.append(match.group(1).rstrip(";").lower())
    return list(reversed(hosts))
