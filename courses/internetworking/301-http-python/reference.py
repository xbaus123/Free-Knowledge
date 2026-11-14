"""An HTTP toolkit: request lines, building requests, status lines, methods, headers, and cookies."""

METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"]
SAFE = {"GET", "HEAD", "OPTIONS", "TRACE"}
IDEMPOTENT = SAFE | {"PUT", "DELETE"}


def parse_request_line(line):
    parts = line.split(" ")
    if len(parts) != 3:
        raise ValueError("a request line has three parts: " + line)
    method, target, version = parts
    if method not in METHODS:
        raise ValueError("unknown method: " + method)
    if not version.startswith("HTTP/") or not target:
        raise ValueError("bad request line: " + line)
    return method, target, version


def build_request(method, host, path="/", headers=None, body=""):
    lines = [method + " " + path + " HTTP/1.1", "Host: " + host]
    for name, value in (headers or []):
        lines.append(name + ": " + value)
    if body:
        lines.append("Content-Length: " + str(len(body.encode("utf-8"))))
    return "\r\n".join(lines) + "\r\n\r\n" + body


def parse_status_line(line):
    parts = line.split(" ", 2)
    if len(parts) < 2 or not parts[0].startswith("HTTP/"):
        raise ValueError("not a status line: " + line)
    code = parts[1]
    if len(code) != 3 or not code.isdigit() or not 100 <= int(code) <= 599:
        raise ValueError("bad status code: " + code)
    reason = parts[2] if len(parts) == 3 else ""
    return parts[0], int(code), reason


CLASSES = {1: "informational", 2: "success", 3: "redirection", 4: "client error", 5: "server error"}


def status_class(code):
    if not 100 <= code <= 599:
        raise ValueError("status codes run from 100 to 599")
    return CLASSES[code // 100]


def is_safe(method):
    return method.upper() in SAFE


def is_idempotent(method):
    return method.upper() in IDEMPOTENT


def parse_headers(lines):
    headers = {}
    for line in lines:
        if ":" not in line:
            raise ValueError("not a header: " + line)
        name, value = line.split(":", 1)
        name, value = name.strip().lower(), value.strip()
        if name in headers:
            headers[name] += ", " + value
        else:
            headers[name] = value
    return headers


def parse_cookies(header):
    cookies = {}
    for piece in header.split(";"):
        piece = piece.strip()
        if "=" not in piece:
            continue
        name, value = piece.split("=", 1)
        cookies[name.strip()] = value.strip()
    return cookies
