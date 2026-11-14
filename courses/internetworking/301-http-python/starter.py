"""An HTTP toolkit: request lines, building requests, status lines, methods, headers, and cookies."""

METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"]


# ---------------------------------------------------------------------------
# Part 1: requests


def parse_request_line(line):
    """Split a request line into (method, target, version).

    parse_request_line("GET /menu.html HTTP/1.1") == ("GET", "/menu.html", "HTTP/1.1")
    Raise ValueError unless there are exactly three space-separated parts,
    the method is one of METHODS, and the version starts with "HTTP/".
    """
    # TODO
    pass


def build_request(method, host, path="/", headers=None, body=""):
    """The full text of a request, with CRLF ("\\r\\n") line endings:

    the request line ("<method> <path> HTTP/1.1"), then "Host: <host>",
    then each (name, value) in headers, in order, then -- only if there is a
    body -- "Content-Length: <body size in UTF-8 bytes>", then a blank line,
    then the body.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 2: responses


def parse_status_line(line):
    """Split a status line into (version, code as an int, reason).

    parse_status_line("HTTP/1.1 404 Not Found") == ("HTTP/1.1", 404, "Not Found")
    The reason may contain spaces, or be missing ("HTTP/2 204" -> reason "").
    Raise ValueError if the version doesn't start with "HTTP/", or the code
    isn't three digits from 100 to 599.
    """
    # TODO
    pass


def status_class(code):
    """The class of a status code, from its first digit:

    1xx "informational", 2xx "success", 3xx "redirection",
    4xx "client error", 5xx "server error".
    Raise ValueError for anything outside 100 to 599.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 3: methods


def is_safe(method):
    """True for the methods that only read: GET, HEAD, OPTIONS, TRACE (any case)."""
    # TODO
    pass


def is_idempotent(method):
    """True if sending it twice has the same effect as once:
    the safe methods, plus PUT and DELETE (any case)."""
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 4: headers and cookies


def parse_headers(lines):
    """Header lines -> a dict of lowercase name -> trimmed value.

    Split each line at its FIRST colon. If a name appears more than once,
    join the values with ", ". Raise ValueError for a line with no colon.
    """
    # TODO
    pass


def parse_cookies(header):
    """The value of a Cookie: header -> a dict.

    parse_cookies("session=8f3a9c2e7b; theme=dark") == {"session": "8f3a9c2e7b", "theme": "dark"}
    Pairs are separated by ";" (with or without spaces); split each pair at its FIRST "=".
    """
    # TODO
    pass


if __name__ == "__main__":
    print(parse_request_line("GET /menu.html HTTP/1.1"))         # ('GET', '/menu.html', 'HTTP/1.1')
    print(repr(build_request("GET", "www.example.com", "/menu.html")))
    # 'GET /menu.html HTTP/1.1\r\nHost: www.example.com\r\n\r\n'
    print(parse_status_line("HTTP/1.1 503 Service Unavailable"))  # ('HTTP/1.1', 503, 'Service Unavailable')
    print(status_class(404))                                      # client error
    print(is_safe("GET"), is_idempotent("POST"))                  # True False
    print(parse_cookies("session=8f3a9c2e7b; theme=dark"))        # {'session': '8f3a9c2e7b', 'theme': 'dark'}
