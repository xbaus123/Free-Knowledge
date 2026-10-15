# FreeKnowledge test harness for Python lessons. Runs solution_test.py with
# unittest and appends one JSON record per test to $FK_RESULTS.
import json
import os
import sys
import time
import traceback
import unittest

RESULTS = os.environ["FK_RESULTS"]


def record(name, status, message="", duration_ms=0):
    with open(RESULTS, "a", encoding="utf-8") as f:
        f.write(json.dumps({"name": name, "status": status, "message": message, "durationMs": duration_ms}) + "\n")


def describe(err):
    exc_type, exc, tb = err
    if isinstance(exc, AssertionError):
        return str(exc) or "assertion failed"
    # Show only the frames in the student's or test's code.
    frames = [f for f in traceback.extract_tb(tb) if os.path.basename(f.filename) in ("solution.py", "solution_test.py")]
    where = "".join(traceback.format_list(frames[-3:]))
    return f"{where}{exc_type.__name__}: {exc}"


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
        record(name(test), "fail", describe(err), self._ms())

    def addError(self, test, err):
        super().addError(test, err)
        record(name(test), "error", describe(err), self._ms())

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        record(name(test), "skip", reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            record(name(subtest), "fail", describe(err), self._ms())


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
