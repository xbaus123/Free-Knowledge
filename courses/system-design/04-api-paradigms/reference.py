"""One bookstore, three APIs: REST, JSON-RPC, and GraphQL."""

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
        self.idempotent = {}  # Idempotency-Key -> the response first sent for it

    def handle(self, method, path, body=None, headers=None):
        url = urlsplit(path)
        parts = [p for p in url.path.split("/") if p]
        if parts == ["books"]:
            if method == "GET":
                return self._list(parse_qs(url.query))
            if method == "POST":
                return self._create(body, headers or {})
            return 405, {"error": f"{method} is not allowed on /books"}
        if len(parts) == 2 and parts[0] == "books":
            if not parts[1].isdigit():
                return 404, {"error": "no such book"}
            id = int(parts[1])
            if method == "GET":
                book = self.store.get_book(id)
                return (200, book) if book else (404, {"error": "no such book"})
            if method == "DELETE":
                return (204, None) if self.store.delete_book(id) else (404, {"error": "no such book"})
            return 405, {"error": f"{method} is not allowed on /books/{id}"}
        return 404, {"error": "not found"}

    def _list(self, query):
        try:
            limit = int(query.get("limit", ["10"])[0])
            after = int(query.get("after", ["0"])[0])
        except ValueError:
            return 400, {"error": "limit and after must be integers"}
        if not 1 <= limit <= 100:
            return 400, {"error": "limit must be between 1 and 100"}
        books = self.store.list_books(after=after, limit=limit + 1)  # one extra: is there more?
        page = books[:limit]
        return 200, {"books": page, "next": page[-1]["id"] if len(books) > limit else None}

    def _create(self, body, headers):
        key = next((v for k, v in headers.items() if k.lower() == "idempotency-key"), None)
        if key is not None and key in self.idempotent:
            return self.idempotent[key]
        error = new_book_error(self.store, body)
        if error:
            return 400, {"error": error}
        response = 201, self.store.add_book(body["title"], body["author_id"], body.get("year"))
        if key is not None:
            self.idempotent[key] = response
        return response


# --- 2. RPC ----------------------------------------------------------------

METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
NOT_FOUND = -32004


class RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class RpcApi:
    def __init__(self, store):
        self.store = store

    def call(self, request):
        reply = {"jsonrpc": "2.0", "id": request.get("id")}
        method = getattr(self, "rpc_" + str(request.get("method")), None)
        try:
            if method is None:
                raise RpcError(METHOD_NOT_FOUND, f"no method {request.get('method')!r}")
            params = request.get("params") or {}
            if not isinstance(params, dict):
                raise RpcError(INVALID_PARAMS, "params must be an object")
            reply["result"] = method(params)
        except RpcError as e:
            reply["error"] = {"code": e.code, "message": str(e)}
        return reply

    def rpc_getBook(self, params):
        id = params.get("id")
        if not isinstance(id, int):
            raise RpcError(INVALID_PARAMS, "id must be an integer")
        book = self.store.get_book(id)
        if book is None:
            raise RpcError(NOT_FOUND, f"no book {id}")
        return book

    def rpc_addBook(self, params):
        error = new_book_error(self.store, params)
        if error:
            raise RpcError(INVALID_PARAMS, error)
        return self.store.add_book(params["title"], params["author_id"], params.get("year"))

    def rpc_booksByAuthor(self, params):
        author_id = params.get("author_id")
        if not isinstance(author_id, int):
            raise RpcError(INVALID_PARAMS, "author_id must be an integer")
        return [b for b in self.store.list_books() if b["author_id"] == author_id]


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
        data = {}
        for f in fields:
            if f.name == "book":
                if not isinstance(f.args.get("id"), int):
                    raise GraphQLError('Field "book" needs an integer argument "id"')
                book = self.store.get_book(f.args["id"])
                data["book"] = self.resolve_books([book], f.fields)[0] if book else None
            else:  # books
                data["books"] = self.resolve_books(self.store.list_books(limit=f.args.get("limit")), f.fields)
        return data

    def resolve_books(self, books, fields):
        authors = {}
        if any(f.name == "author" for f in fields):
            # One query for every author on the page, not one per book.
            authors = self.store.get_authors(sorted({b["author_id"] for b in books}))
        out = []
        for book in books:
            item = {}
            for f in fields:
                if f.name == "author":
                    author = authors[book["author_id"]]
                    item["author"] = {sub.name: author[sub.name] for sub in f.fields}
                else:
                    item[f.name] = book[f.name]
            out.append(item)
        return out


def validate(type_name, fields):
    """Checks a selection set against SCHEMA before anything runs."""
    for f in fields:
        if f.name not in SCHEMA[type_name]:
            raise GraphQLError(f'Cannot query field "{f.name}" on type "{type_name}"')
        child = SCHEMA[type_name][f.name]
        if child and not f.fields:
            raise GraphQLError(f'Field "{f.name}" of type "{child}" must have a selection of subfields')
        if not child and f.fields:
            raise GraphQLError(f'Field "{f.name}" is a scalar and can\'t have subfields')
        if child:
            validate(child, f.fields)
