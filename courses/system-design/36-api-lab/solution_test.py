import unittest

import solution
from solution import GraphQLApi, RestApi, RpcApi


class Store:
    """The same interface as solution.Store, owned by the tests."""

    def __init__(self):
        self.authors = {1: {"id": 1, "name": "Octavia Butler"}, 2: {"id": 2, "name": "N. K. Jemisin"}, 3: {"id": 3, "name": "Liu Cixin"}}
        self.books = {
            1: {"id": 1, "title": "Kindred", "year": 1979, "author_id": 1},
            2: {"id": 2, "title": "Parable of the Sower", "year": 1993, "author_id": 1},
            3: {"id": 3, "title": "The Fifth Season", "year": 2015, "author_id": 2},
            4: {"id": 4, "title": "The Obelisk Gate", "year": 2016, "author_id": 2},
            5: {"id": 5, "title": "The Three-Body Problem", "year": 2008, "author_id": 3},
            6: {"id": 6, "title": "The Dark Forest", "year": 2008, "author_id": 3},
            7: {"id": 7, "title": "Dawn", "year": 1987, "author_id": 1},
        }
        self.calls = 0

    def get_book(self, id):
        self.calls += 1
        book = self.books.get(id)
        return dict(book) if book else None

    def list_books(self, after=0, limit=None):
        self.calls += 1
        ids = sorted(i for i in self.books if i > after)
        return [dict(self.books[i]) for i in ids[:limit]]

    def add_book(self, title, author_id, year=None):
        self.calls += 1
        id = max(self.books, default=0) + 1
        self.books[id] = {"id": id, "title": title, "year": year, "author_id": author_id}
        return dict(self.books[id])

    def delete_book(self, id):
        self.calls += 1
        return self.books.pop(id, None) is not None

    def get_author(self, id):
        self.calls += 1
        author = self.authors.get(id)
        return dict(author) if author else None

    def get_authors(self, ids):
        self.calls += 1
        return {i: dict(self.authors[i]) for i in ids if i in self.authors}


KINDRED = {"id": 1, "title": "Kindred", "year": 1979, "author_id": 1}


class RestTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.api = RestApi(self.store)

    def ids(self, body):
        return [b["id"] for b in body["books"]]

    def test_get_one(self):
        """GET /books/{id} returns 200 and the book, or 404"""
        self.assertEqual(self.api.handle("GET", "/books/1"), (200, KINDRED))
        status, body = self.api.handle("GET", "/books/99")
        self.assertEqual(status, 404)
        self.assertIn("error", body)
        self.assertEqual(self.api.handle("GET", "/books/abc")[0], 404)

    def test_pagination(self):
        """GET /books pages through the collection with a cursor"""
        status, body = self.api.handle("GET", "/books?limit=3")
        self.assertEqual((status, self.ids(body), body["next"]), (200, [1, 2, 3], 3))
        status, body = self.api.handle("GET", "/books?limit=3&after=3")
        self.assertEqual((self.ids(body), body["next"]), ([4, 5, 6], 6))
        status, body = self.api.handle("GET", "/books?limit=3&after=6")
        self.assertEqual((self.ids(body), body["next"]), ([7], None), "the last page has no next cursor")
        status, body = self.api.handle("GET", "/books?limit=7")
        self.assertEqual((self.ids(body), body["next"]), ([1, 2, 3, 4, 5, 6, 7], None), "no next page when nothing is left")
        status, body = self.api.handle("GET", "/books")
        self.assertEqual(len(body["books"]), 7, "the default limit is 10")
        self.assertEqual(body["books"][0], KINDRED)

    def test_bad_limit(self):
        """rejects a limit outside 1 to 100 with 400"""
        for query in ("limit=0", "limit=101", "limit=ten", "after=x"):
            self.assertEqual(self.api.handle("GET", "/books?" + query)[0], 400, query)

    def test_create(self):
        """POST /books creates a book and returns 201"""
        status, body = self.api.handle("POST", "/books", {"title": "Binti", "author_id": 2, "year": 2015})
        self.assertEqual(status, 201)
        self.assertEqual(body, {"id": 8, "title": "Binti", "year": 2015, "author_id": 2})
        self.assertEqual(self.api.handle("GET", "/books/8"), (200, body))

    def test_create_validates(self):
        """rejects an invalid book with 400 and creates nothing"""
        for body in ({"author_id": 1}, {"title": "  ", "author_id": 1}, {"title": "X", "author_id": 42}, None):
            status, reply = self.api.handle("POST", "/books", body)
            self.assertEqual(status, 400, body)
            self.assertIn("error", reply)
        self.assertEqual(len(self.store.books), 7)

    def test_idempotency_key(self):
        """replays the first response for a repeated Idempotency-Key"""
        book = {"title": "Lilith's Brood", "author_id": 1}
        first = self.api.handle("POST", "/books", book, {"Idempotency-Key": "abc"})
        again = self.api.handle("POST", "/books", book, {"Idempotency-Key": "abc"})
        self.assertEqual(first[0], 201)
        self.assertEqual(again, first, "a retry with the same key must not create a second book")
        self.assertEqual(len(self.store.books), 8)
        self.api.handle("POST", "/books", book, {"Idempotency-Key": "def"})
        self.api.handle("POST", "/books", book)
        self.assertEqual(len(self.store.books), 10, "different keys, or no key, create new books")

    def test_delete(self):
        """DELETE /books/{id} returns 204, then 404"""
        self.assertEqual(self.api.handle("DELETE", "/books/1"), (204, None))
        self.assertEqual(self.api.handle("DELETE", "/books/1")[0], 404)
        self.assertEqual(self.api.handle("GET", "/books/1")[0], 404)

    def test_wrong_method_or_path(self):
        """answers 405 for a method a resource doesn't support and 404 for an unknown path"""
        for method, path in (("PUT", "/books/1"), ("POST", "/books/1"), ("DELETE", "/books"), ("PATCH", "/books")):
            self.assertEqual(self.api.handle(method, path, {})[0], 405, f"{method} {path}")
        for path in ("/", "/authors", "/books/1/reviews"):
            self.assertEqual(self.api.handle("GET", path)[0], 404, path)


class RpcTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.api = RpcApi(self.store)

    def call(self, method, params, id=1):
        return self.api.call({"jsonrpc": "2.0", "method": method, "params": params, "id": id})

    def test_get_book(self):
        """getBook returns the result with the request's id"""
        self.assertEqual(self.call("getBook", {"id": 1}, id=7), {"jsonrpc": "2.0", "id": 7, "result": KINDRED})

    def test_errors(self):
        """reports errors with JSON-RPC codes"""
        reply = self.call("getBook", {"id": 99}, id=3)
        self.assertEqual((reply["id"], reply["error"]["code"]), (3, solution.NOT_FOUND))
        self.assertNotIn("result", reply)
        self.assertEqual(self.call("deleteEverything", {})["error"]["code"], solution.METHOD_NOT_FOUND)
        self.assertEqual(self.call("getBook", {})["error"]["code"], solution.INVALID_PARAMS)
        self.assertEqual(self.call("getBook", {"id": "one"})["error"]["code"], solution.INVALID_PARAMS)
        self.assertIn("message", self.call("getBook", {})["error"])

    def test_add_book(self):
        """addBook creates a book or reports invalid params"""
        reply = self.call("addBook", {"title": "Binti", "author_id": 2})
        self.assertEqual(reply["result"], {"id": 8, "title": "Binti", "year": None, "author_id": 2})
        self.assertEqual(self.call("addBook", {"title": "", "author_id": 2})["error"]["code"], solution.INVALID_PARAMS)
        self.assertEqual(self.call("addBook", {"title": "X", "author_id": 9})["error"]["code"], solution.INVALID_PARAMS)
        self.assertEqual(len(self.store.books), 8)

    def test_books_by_author(self):
        """booksByAuthor returns an author's books in id order"""
        reply = self.call("booksByAuthor", {"author_id": 1})
        self.assertEqual([b["id"] for b in reply["result"]], [1, 2, 7])
        self.assertEqual(self.call("booksByAuthor", {"author_id": 42})["result"], [])


class GraphQLTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.api = GraphQLApi(self.store)

    def run_query(self, query):
        return self.api.execute(query)

    def test_only_requested_fields(self):
        """returns exactly the fields the query asks for"""
        self.assertEqual(self.run_query("{ book(id: 3) { title } }"), {"data": {"book": {"title": "The Fifth Season"}}})
        self.assertEqual(
            self.run_query("{ book(id: 3) { id year title } }"),
            {"data": {"book": {"id": 3, "year": 2015, "title": "The Fifth Season"}}},
        )

    def test_nested(self):
        """resolves a book's author"""
        self.assertEqual(
            self.run_query("query { book(id: 5) { title author { name } } }"),
            {"data": {"book": {"title": "The Three-Body Problem", "author": {"name": "Liu Cixin"}}}},
        )
        self.assertEqual(self.run_query("{ book(id: 99) { title } }"), {"data": {"book": None}})

    def test_lists(self):
        """resolves lists and several top-level fields"""
        result = self.run_query("{ books(limit: 2) { id } book(id: 7) { title } }")
        self.assertEqual(result, {"data": {"books": [{"id": 1}, {"id": 2}], "book": {"title": "Dawn"}}})
        self.assertEqual(len(self.run_query("{ books { id } }")["data"]["books"]), 7)

    def test_no_n_plus_one(self):
        """loads a page of books and their authors in two queries"""
        result = self.run_query("{ books(limit: 5) { title author { id name } } }")
        books = result["data"]["books"]
        self.assertEqual([b["author"]["name"] for b in books], ["Octavia Butler"] * 2 + ["N. K. Jemisin"] * 2 + ["Liu Cixin"])
        self.assertEqual(books[2], {"title": "The Fifth Season", "author": {"id": 2, "name": "N. K. Jemisin"}})
        self.assertLessEqual(self.store.calls, 2, "one query for the books, one for all their authors (not one per book)")
        self.store.calls = 0
        self.run_query("{ books { title } }")
        self.assertEqual(self.store.calls, 1, "don't load authors nobody asked for")

    def test_validation(self):
        """rejects fields the schema doesn't have, before running anything"""
        for query, word in (
            ("{ book(id: 1) { title isbn } }", "isbn"),
            ("{ authors { name } }", "authors"),
            ("{ books(limit: 1) { author { name email } } }", "email"),
            ("{ book(id: 1) { author } }", "author"),
            ("{ book(id: 1) { title { length } } }", "title"),
        ):
            self.store.calls = 0
            result = self.run_query(query)
            self.assertNotIn("data", result, query)
            self.assertIn(word, result["errors"][0]["message"], query)
            self.assertEqual(self.store.calls, 0, f"validate {query} before querying the store")

    def test_syntax_errors(self):
        """reports a syntax error"""
        self.assertIn("errors", self.run_query("{ book(id: 1) { title }"))


if __name__ == "__main__":
    unittest.main()
