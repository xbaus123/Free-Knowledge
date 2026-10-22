# FreeKnowledge test harness for Python lessons. Runs solution_test.py with
# unittest and appends one JSON record per test to $FK_RESULTS.
import ast
import functools
import inspect
import json
import os
import pprint
import re
import sys
import time
import traceback
import unittest

RESULTS = os.environ["FK_RESULTS"]
TEST_FILE = "solution_test.py"
MAX_VALUE = 2000  # characters of input/expected/actual to show
WORKSPACE = os.path.realpath(os.getcwd())


def record(name, status, message="", duration_ms=0, details=None):
    rec = {"name": name, "status": status, "message": message, "durationMs": duration_ms}
    rec.update(details or {})
    with open(RESULTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def describe(err):
    exc_type, exc, tb = err
    if isinstance(exc, AssertionError):
        return str(exc) or "assertion failed"
    # Show only the frames in the student's or test's code.
    frames = [f for f in traceback.extract_tb(tb) if os.path.basename(f.filename) in ("solution.py", TEST_FILE)]
    where = "".join(traceback.format_list(frames[-3:]))
    return f"{where}{exc_type.__name__}: {exc}"


# --- structured failure details ---
#
# The assertion methods below are wrapped so a failure carries the compared
# values (actual and expected) and, when the assertion's source shows a call
# into the learner's code, that call with its arguments (input).

def show(value):
    text = repr(value) if isinstance(value, str) else pprint.pformat(value, width=72, sort_dicts=False)
    return text if len(text) <= MAX_VALUE else text[:MAX_VALUE] + "…"


def opaque(text):
    """Default reprs like <Foo object at 0x10> say nothing; show source instead."""
    return re.search(r" at 0x[0-9a-f]+>", text) is not None


@functools.cache
def test_tree(path):
    try:
        with open(path, encoding="utf-8") as f:
            return ast.parse(f.read())
    except (OSError, SyntaxError):
        return None


def test_frame(frame):
    while frame is not None and os.path.basename(frame.f_code.co_filename) != TEST_FILE:
        frame = frame.f_back
    return frame


def assertion_node(frame):
    """The self.assert…(...) call on the frame's current line, if any."""
    tree = test_tree(frame.f_code.co_filename)
    if tree is None:
        return None
    line = frame.f_lineno
    best = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr.startswith("assert")
            and node.lineno <= line <= (node.end_lineno or node.lineno)
            and (best is None or node.lineno >= best.lineno)
        ):
            best = node
    return best


MISSING = object()


def lookup(node, frame):
    """Evaluates names, attributes, subscripts and literals without calling anything."""
    if isinstance(node, ast.Name):
        for scope in (frame.f_locals, frame.f_globals, frame.f_builtins):
            if node.id in scope:
                return scope[node.id]
        return MISSING
    if isinstance(node, ast.Attribute):
        base = lookup(node.value, frame)
        return MISSING if base is MISSING else getattr(base, node.attr, MISSING)
    if isinstance(node, ast.Subscript):
        base, key = lookup(node.value, frame), lookup(node.slice, frame)
        if MISSING in (base, key):
            return MISSING
        try:
            return base[key]
        except Exception:
            return MISSING
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return MISSING


def learner_module(name):
    if name in (None, "solution_test", "__main__") or not isinstance(name, str):
        return False
    path = getattr(sys.modules.get(name), "__file__", None)
    return bool(path) and os.path.realpath(path).startswith(WORKSPACE + os.sep)


def learner_call(node, frame):
    """The outermost call in node whose function is defined in the learner's code."""
    if node is None:
        return None
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            fn = lookup(sub.func, frame)
            if fn is not MISSING and learner_module(getattr(fn, "__module__", None)):
                return sub
    return None


def render_value(value, source):
    if value is MISSING:
        return source
    text = show(value)
    return source if opaque(text) else text


def render_arg(node, frame):
    return render_value(lookup(node, frame), ast.unparse(node))


def render_call(call, frame):
    func = call.func
    # solution.fn(...) reads better as fn(...).
    if isinstance(func, ast.Attribute) and inspect.ismodule(lookup(func.value, frame)):
        name = func.attr
    else:
        name = ast.unparse(func)
    parts = []
    for arg in call.args:
        if isinstance(arg, ast.Starred):
            value = lookup(arg.value, frame)
            if isinstance(value, (list, tuple)):
                parts.extend(render_value(v, "…") for v in value)
                continue
            parts.append("*" + render_arg(arg.value, frame))
        else:
            parts.append(render_arg(arg, frame))
    for kw in call.keywords:
        parts.append(f"{kw.arg}={render_arg(kw.value, frame)}" if kw.arg else "**" + render_arg(kw.value, frame))
    text = f"{name}({', '.join(parts)})"
    return text if len(text) <= MAX_VALUE else text[:MAX_VALUE] + "…"


def failure_details(test, frame, actual, expected, compared=2):
    """actual/expected come in source order (first, second); compared is how
    many leading arguments of the assertion they are."""
    details = {}
    frame = test_frame(frame)
    node = assertion_node(frame) if frame is not None else None
    args = node.args if node is not None else []
    first = args[0] if len(args) > 0 else None
    second = args[1] if len(args) > 1 and compared > 1 else None
    call = learner_call(first, frame) if frame is not None else None
    # Tests usually say assertEqual(actual, expected); accept the reverse
    # when only the second argument calls the learner's code.
    if call is None and frame is not None:
        swapped = learner_call(second, frame)
        if swapped is not None:
            call, actual, expected = swapped, expected, actual
    if call is not None:
        details["input"] = render_call(call, frame)
    else:
        sub = getattr(test, "_subtest", None)
        params = getattr(sub, "params", None)
        if params:
            details["input"] = ", ".join(f"{k}={show(v)}" for k, v in params.items())
    details["expected"] = expected
    details["actual"] = actual
    return details


# Assertion name → (actual, expected, compared) from its arguments in order.
# Delegates like assertDictEqual(d1, d2) name their parameters differently,
# so arguments are taken by position.
def _pair(a):
    return a[0], a[1], 2


def _none(a):
    return a[0], None, 1


def _bool(want):
    def pick(a):
        return (a[0], want, 1) if isinstance(a[0], bool) else None
    return pick


CAPTURED = {
    "assertEqual": _pair,
    "assertAlmostEqual": _pair,
    "assertCountEqual": _pair,
    "assertListEqual": _pair,
    "assertTupleEqual": _pair,
    "assertDictEqual": _pair,
    "assertSetEqual": _pair,
    "assertSequenceEqual": _pair,
    "assertMultiLineEqual": _pair,
    "assertIs": _pair,
    "assertIsNone": _none,
    "assertTrue": _bool(True),
    "assertFalse": _bool(False),
}


def capturing(method, pick):
    signature = inspect.signature(method)

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except AssertionError as exc:
            # assertEqual delegates to assertListEqual etc.; the outer call's
            # frame is the one in the test, and both see the same values.
            if not hasattr(exc, "fk_details"):
                try:
                    bound = signature.bind(self, *args, **kwargs).arguments
                    picked = pick(list(bound.values())[1:])
                    if picked is not None:
                        actual, expected, compared = picked
                        details = failure_details(self, sys._getframe(1), show(actual), show(expected), compared)
                        exc.fk_details = details
                except Exception:
                    pass  # never let reporting hide the real failure
            raise

    return wrapper


for _name, _pick in CAPTURED.items():
    setattr(unittest.TestCase, _name, capturing(getattr(unittest.TestCase, _name), _pick))


def details_of(err):
    return getattr(err[1], "fk_details", None)


class Result(unittest.TestResult):
    def startTest(self, test):
        super().startTest(test)
        self._start = time.perf_counter()

    def _ms(self):
        return int((time.perf_counter() - self._start) * 1000)

    def addSuccess(self, test):
        super().addSuccess(test)
        record(name(test), "pass", duration_ms=self._ms())

    def addFailure(self, test, err):
        super().addFailure(test, err)
        record(name(test), "fail", describe(err), self._ms(), details_of(err))

    def addError(self, test, err):
        super().addError(test, err)
        record(name(test), "error", describe(err), self._ms())

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        record(name(test), "skip", reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            record(name(subtest), "fail", describe(err), self._ms(), details_of(err))


def name(test):
    desc = test.shortDescription()
    return desc or test.id().removeprefix("solution_test.")


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def source_line(test):
    try:
        return getattr(type(test), test._testMethodName).__code__.co_firstlineno
    except AttributeError:
        return 0


def main():
    sys.path.insert(0, os.getcwd())
    try:
        import solution_test  # noqa: F401  (also imports the student's solution)
    except Exception:
        traceback.print_exc()
        sys.exit(2)
    loaded = unittest.defaultTestLoader.loadTestsFromModule(solution_test)
    # Run in the order tests are written, not alphabetically.
    suite = unittest.TestSuite(sorted(flatten(loaded), key=source_line))
    result = Result()
    suite.run(result)
    sys.stdout.flush()
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
