import unittest

from solution import (build_request, is_idempotent, is_safe, parse_cookies, parse_headers, parse_request_line,
                      parse_status_line, status_class)


class ParseRequestLine(unittest.TestCase):
    def test_reading_example(self):
        """GET /menu.html HTTP/1.1, from the reading"""
        self.assertEqual(parse_request_line("GET /menu.html HTTP/1.1"), ("GET", "/menu.html", "HTTP/1.1"))

    def test_other_methods(self):
        """Every one of the nine methods is accepted"""
        for m in ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"]:
            self.assertEqual(parse_request_line(m + " / HTTP/1.1")[0], m)

    def test_connect_target(self):
        """CONNECT names a host and port, not a path"""
        self.assertEqual(parse_request_line("CONNECT bank.example:443 HTTP/1.1"),
                         ("CONNECT", "bank.example:443", "HTTP/1.1"))

    def test_query_string(self):
        """The target keeps its query string"""
        self.assertEqual(parse_request_line("GET /search?q=pizza HTTP/1.1")[1], "/search?q=pizza")

    def test_unknown_method(self):
        """FETCH isn't an HTTP method"""
        with self.assertRaises(ValueError):
            parse_request_line("FETCH / HTTP/1.1")

    def test_wrong_parts(self):
        """Too few or too many parts, or no HTTP/ version"""
        for bad in ["GET /", "GET / HTTP/1.1 extra", "GET / FTP/1.0", ""]:
            with self.assertRaises(ValueError):
                parse_request_line(bad)


class BuildRequest(unittest.TestCase):
    def test_simple_get(self):
        """Request line, Host, blank line"""
        self.assertEqual(build_request("GET", "www.example.com", "/menu.html"),
                         "GET /menu.html HTTP/1.1\r\nHost: www.example.com\r\n\r\n")

    def test_default_path(self):
        """No path means /"""
        self.assertTrue(build_request("HEAD", "example.com").startswith("HEAD / HTTP/1.1\r\n"))

    def test_headers_in_order(self):
        """Extra headers follow Host, in the order given"""
        req = build_request("GET", "shop.example.com", "/account",
                            [("Cookie", "session=8f3a9c2e7b"), ("Accept", "text/html")])
        self.assertEqual(req, "GET /account HTTP/1.1\r\nHost: shop.example.com\r\n"
                              "Cookie: session=8f3a9c2e7b\r\nAccept: text/html\r\n\r\n")

    def test_body_gets_length(self):
        """A body adds Content-Length, after the other headers"""
        req = build_request("POST", "api.example.com", "/users", [("Content-Type", "application/json")],
                            '{"name": "Alice"}')
        self.assertEqual(req, "POST /users HTTP/1.1\r\nHost: api.example.com\r\n"
                              "Content-Type: application/json\r\nContent-Length: 17\r\n\r\n"
                              '{"name": "Alice"}')

    def test_length_is_bytes(self):
        """Content-Length counts UTF-8 bytes, not characters: é is two bytes"""
        req = build_request("POST", "x.example", "/", body="café")
        self.assertIn("Content-Length: 5\r\n", req)


class ParseStatusLine(unittest.TestCase):
    def test_ok(self):
        """HTTP/1.1 200 OK"""
        self.assertEqual(parse_status_line("HTTP/1.1 200 OK"), ("HTTP/1.1", 200, "OK"))

    def test_reason_with_spaces(self):
        """The reason can have spaces"""
        self.assertEqual(parse_status_line("HTTP/1.1 503 Service Unavailable"),
                         ("HTTP/1.1", 503, "Service Unavailable"))

    def test_no_reason(self):
        """The reason is optional"""
        self.assertEqual(parse_status_line("HTTP/2 204"), ("HTTP/2", 204, ""))

    def test_bad(self):
        """No version, a code that isn't three digits, or out of range"""
        for bad in ["200 OK", "HTTP/1.1 20 OK", "HTTP/1.1 OK", "HTTP/1.1 600 Nope", "HTTP/1.1 099 Low"]:
            with self.assertRaises(ValueError):
                parse_status_line(bad)


class StatusClass(unittest.TestCase):
    def test_each_class(self):
        """The first digit decides"""
        self.assertEqual(status_class(100), "informational")
        self.assertEqual(status_class(201), "success")
        self.assertEqual(status_class(304), "redirection")
        self.assertEqual(status_class(404), "client error")
        self.assertEqual(status_class(502), "server error")

    def test_edges(self):
        """199 and 599 are still in range"""
        self.assertEqual(status_class(199), "informational")
        self.assertEqual(status_class(599), "server error")

    def test_out_of_range(self):
        """Nothing below 100 or above 599"""
        for bad in [0, 99, 600, 1000]:
            with self.assertRaises(ValueError):
                status_class(bad)


class MethodProperties(unittest.TestCase):
    def test_safe(self):
        """GET, HEAD, OPTIONS, and TRACE only read"""
        for m in ["GET", "HEAD", "OPTIONS", "TRACE"]:
            self.assertTrue(is_safe(m), m)
        for m in ["POST", "PUT", "PATCH", "DELETE", "CONNECT"]:
            self.assertFalse(is_safe(m), m)

    def test_idempotent(self):
        """The safe methods plus PUT and DELETE"""
        for m in ["GET", "HEAD", "OPTIONS", "TRACE", "PUT", "DELETE"]:
            self.assertTrue(is_idempotent(m), m)
        for m in ["POST", "PATCH", "CONNECT"]:
            self.assertFalse(is_idempotent(m), m)

    def test_case(self):
        """Method names are compared in upper case"""
        self.assertTrue(is_safe("get"))
        self.assertTrue(is_idempotent("Delete"))

    def test_unknown(self):
        """An unknown method is neither"""
        self.assertFalse(is_safe("FETCH"))
        self.assertFalse(is_idempotent("FETCH"))


class ParseHeaders(unittest.TestCase):
    def test_reading_response(self):
        """The response headers from the reading"""
        self.assertEqual(parse_headers(["Content-Type: text/html; charset=utf-8", "Content-Length: 1834"]),
                         {"content-type": "text/html; charset=utf-8", "content-length": "1834"})

    def test_case_and_spaces(self):
        """Names are lowercased, values trimmed"""
        self.assertEqual(parse_headers(["HOST:   www.example.com  "]), {"host": "www.example.com"})

    def test_colon_in_value(self):
        """Only the first colon splits"""
        self.assertEqual(parse_headers(["Location: https://example.com:8443/login"]),
                         {"location": "https://example.com:8443/login"})

    def test_repeated(self):
        """A repeated header is joined with a comma"""
        self.assertEqual(parse_headers(["Accept-Encoding: gzip", "accept-encoding: br"]),
                         {"accept-encoding": "gzip, br"})

    def test_not_a_header(self):
        """No colon, no header"""
        with self.assertRaises(ValueError):
            parse_headers(["Host www.example.com"])


class ParseCookies(unittest.TestCase):
    def test_reading_example(self):
        """Cookie: session=8f3a9c2e7b"""
        self.assertEqual(parse_cookies("session=8f3a9c2e7b"), {"session": "8f3a9c2e7b"})

    def test_several(self):
        """Pairs are separated by ; and spaces"""
        self.assertEqual(parse_cookies("session=8f3a9c2e7b; theme=dark;lang=en"),
                         {"session": "8f3a9c2e7b", "theme": "dark", "lang": "en"})

    def test_equals_in_value(self):
        """Only the first = splits a pair"""
        self.assertEqual(parse_cookies("token=abc==; x=1"), {"token": "abc==", "x": "1"})

    def test_empty(self):
        """No cookies at all"""
        self.assertEqual(parse_cookies(""), {})


if __name__ == "__main__":
    unittest.main()
