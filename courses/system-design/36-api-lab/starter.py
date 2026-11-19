"""One bookstore, three APIs: REST, JSON-RPC, and GraphQL.

The Store, the sample data, new_book_error, and the GraphQL parser are
provided. Build RestApi, RpcApi, and GraphQLApi on top of them; the lesson
describes exactly what each should do.
"""

import json
import re
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlsplit


# --- The data (provided) ---------------------------------------------------


class Store:
    """The database behind all three APIs. Every method call counts as one
    query in self.calls."""

    def __init__(self, authors, books):
        self.authors = {a["id"]: dict(a) for a in authors}
        self.books = {b["id"]: dict(b) for b in books}
        self.calls = 0

    def get_book(self, id):
        self.calls += 1
        book = self.books.get(id)
        return dict(book) if book else None

    def list_books(self, after=0, limit=None):
        """Books with id > after, in id order, at most limit of them."""
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
        """Many authors in one query: {id: author} for the ids that exist."""
        self.calls += 1
        return {i: dict(self.authors[i]) for i in ids if i in self.authors}


SAMPLE = Store(
    authors=[{"id": 1, "name": "Ursula K. Le Guin"}, {"id": 2, "name": "Ted Chiang"}],
    books=[
        {"id": 1, "title": "A Wizard of Earthsea", "year": 1968, "author_id": 1},
        {"id": 2, "title": "The Dispossessed", "year": 1974, "author_id": 1},
        {"id": 3, "title": "Stories of Your Life and Others", "year": 2002, "author_id": 2},
        {"id": 4, "title": "Exhalation", "year": 2019, "author_id": 2},
    ],
)


def new_book_error(store, body):
    """Validates a new book's fields (title, author_id, and an optional
    year). Returns an error message, or None if they're fine."""
    if not isinstance(body, dict):
        return "the body must be a JSON object"
    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        return "title is required"
    author_id = body.get("author_id")
    if not isinstance(author_id, int) or store.get_author(author_id) is None:
        return "author_id must be an existing author"
    year = body.get("year")
    if year is not None and not isinstance(year, int):
        return "year must be an integer"
    return None


# --- 1. REST ---------------------------------------------------------------


class RestApi:
    def __init__(self, store):
        self.store = store

    def handle(self, method, path, body=None, headers=None):
        """Handle one HTTP request. Return (status, body).

        GET /books?limit=&after=, POST /books, GET /books/{id}, and
        DELETE /books/{id}.
        """
        return 501, {"error": "not implemented"}


# --- 2. RPC ----------------------------------------------------------------

METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
NOT_FOUND = -32004


class RpcApi:
    def __init__(self, store):
        self.store = store

    def call(self, request):
        """Handle one JSON-RPC request:
        {"jsonrpc": "2.0", "method": "getBook", "params": {"id": 2}, "id": 7}.

        Methods: getBook, addBook, booksByAuthor.
        """
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": METHOD_NOT_FOUND, "message": "not implemented"},
        }


# --- 3. GraphQL --------------------------------------------------------------

# Each type's fields, and the type of the object each one returns (None for
# a scalar like a number or a string).
SCHEMA = {
    "Query": {"book": "Book", "books": "Book"},
    "Book": {"id": None, "title": None, "year": None, "author": "Author"},
    "Author": {"id": None, "name": None},
}


class GraphQLError(Exception):
    pass


@dataclass
class Field:
    name: str
    args: dict = field(default_factory=dict)
    fields: list = field(default_factory=list)  # the selection set; empty for a scalar


def parse(query):
    """Parses a GraphQL query such as '{ book(id: 2) { title } }' into a
    list of its top-level Fields. Raises GraphQLError on bad syntax."""
    return _Parser(query).document()


class _Parser:
    TOKEN = re.compile(r'[{}():]|"(?:[^"\\]|\\.)*"|-?\d+|[A-Za-z_]\w*')
    SKIP = re.compile(r"[\s,]*")  # GraphQL treats commas as whitespace

    def __init__(self, text):
        self.tokens, pos = [], 0
        while (pos := self.SKIP.match(text, pos).end()) < len(text):
            m = self.TOKEN.match(text, pos)
            if not m:
                raise GraphQLError(f"Syntax error: unexpected {text[pos]!r}")
            self.tokens.append(m.group())
            pos = m.end()
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self, want=None):
        tok = self.peek()
        if tok is None or (want is not None and tok != want):
            raise GraphQLError(f"Syntax error: expected {want or 'more'}, got {tok or 'end of query'}")
        self.i += 1
        return tok

    def document(self):
        if self.peek() == "query":
            self.take()
            if self.peek() != "{":
                self.name()  # an operation name
        fields = self.selection_set()
        if self.peek() is not None:
            raise GraphQLError(f"Syntax error: unexpected {self.peek()}")
        return fields

    def name(self):
        tok = self.take()
        if not re.fullmatch(r"[A-Za-z_]\w*", tok):
            raise GraphQLError(f"Syntax error: expected a name, got {tok}")
        return tok

    def selection_set(self):
        self.take("{")
        fields = []
        while self.peek() != "}":
            fields.append(self.field())
        self.take("}")
        return fields

    def field(self):
        name, args = self.name(), {}
        if self.peek() == "(":
            self.take("(")
            while self.peek() != ")":
                key = self.name()
                self.take(":")
                args[key] = self.value()
            self.take(")")
        fields = self.selection_set() if self.peek() == "{" else []
        return Field(name, args, fields)

    def value(self):
        tok = self.take()
        if tok.startswith('"'):
            return json.loads(tok)
        if re.fullmatch(r"-?\d+", tok):
            return int(tok)
        if tok in ("true", "false", "null"):
            return {"true": True, "false": False, "null": None}[tok]
        raise GraphQLError(f"Syntax error: unexpected {tok}")


class GraphQLApi:
    def __init__(self, store):
        self.store = store

    def execute(self, query):
        try:
            fields = parse(query)
            validate("Query", fields)
            return {"data": self.resolve_query(fields)}
        except GraphQLError as e:
            return {"errors": [{"message": str(e)}]}

    def resolve_query(self, fields):
        """Return the data for the top-level fields: book(id:) and books(limit:).

        Include exactly the fields each selection asks for, and load the
        authors for a list of books in one query.
        """
        return {}


def validate(type_name, fields):
    """Check a selection set against SCHEMA before anything runs. Raise
    GraphQLError for a field the type doesn't have, an object field with no
    subfields, or a scalar field with subfields."""
