import json
import random
import re
import unittest

import solution
from solution import Counter, Histogram, SpanContext, Tracer, critical_path, extract, inject


def latency_histogram():
    h = Histogram("http_request_duration_seconds", "Request latency.", [0.1, 0.25, 0.5, 1])
    for v in [0.05] * 4 + [0.2] * 4 + [0.4, 0.8]:
        h.observe(v, route="/home")
    return h


class HistogramTest(unittest.TestCase):
    def test_quantiles(self):
        """estimates percentiles by interpolating within buckets"""
        h = latency_histogram()
        self.assertAlmostEqual(h.quantile(0.2, route="/home"), 0.05)  # rank 2 of 4 in (0, 0.1]
        self.assertAlmostEqual(h.quantile(0.5, route="/home"), 0.1375)  # rank 5: 1 of 4 into (0.1, 0.25]
        self.assertAlmostEqual(h.quantile(0.9, route="/home"), 0.5)
        self.assertAlmostEqual(h.quantile(0.99, route="/home"), 0.95)

    def test_overflow_bucket(self):
        """reports the highest finite bound for the +Inf bucket"""
        h = latency_histogram()
        h.observe(7.5, route="/home")
        self.assertEqual(h.quantile(1.0, route="/home"), 1)

    def test_label_sets(self):
        """keeps a separate series per label set"""
        h = latency_histogram()
        h.observe(0.9, route="/search")
        self.assertAlmostEqual(h.quantile(0.5, route="/search"), 0.75)
        self.assertIsNone(h.quantile(0.5, route="/nowhere"))
        self.assertAlmostEqual(h.quantile(0.5, route="/home"), 0.1375, "/search didn't change /home")

    def test_bucket_edges(self):
        """counts a value equal to a bound in that bound's bucket"""
        h = Histogram("x", "x", [1, 2])
        h.observe(1)
        self.assertAlmostEqual(h.quantile(1.0), 1, msg="1 belongs in le=1")


class RenderTest(unittest.TestCase):
    def test_counter(self):
        """renders counters with sorted labels"""
        c = Counter("http_requests_total", "Requests handled.")
        c.inc(status="200", method="GET")
        c.inc(2, method="GET", status="200")
        c.inc(method="POST", status="500")
        self.assertEqual(
            solution.render([c]),
            "# HELP http_requests_total Requests handled.\n"
            "# TYPE http_requests_total counter\n"
            'http_requests_total{method="GET",status="200"} 3\n'
            'http_requests_total{method="POST",status="500"} 1\n',
        )

    def test_histogram(self):
        """renders cumulative buckets, sum, and count"""
        h = latency_histogram()
        self.assertEqual(
            solution.render([h]),
            "# HELP http_request_duration_seconds Request latency.\n"
            "# TYPE http_request_duration_seconds histogram\n"
            'http_request_duration_seconds_bucket{route="/home",le="0.1"} 4\n'
            'http_request_duration_seconds_bucket{route="/home",le="0.25"} 8\n'
            'http_request_duration_seconds_bucket{route="/home",le="0.5"} 9\n'
            'http_request_duration_seconds_bucket{route="/home",le="1"} 10\n'
            'http_request_duration_seconds_bucket{route="/home",le="+Inf"} 10\n'
            'http_request_duration_seconds_sum{route="/home"} 2.2\n'
            'http_request_duration_seconds_count{route="/home"} 10\n',
        )

    def test_unlabeled_and_several(self):
        """renders unlabeled series and several metrics in order"""
        jobs = Counter("jobs_total", "Jobs run.")
        jobs.inc(5)
        size = Histogram("batch_size", "Items per batch.", [10])
        size.observe(4)
        size.observe(40)
        self.assertEqual(
            solution.render([jobs, size]),
            "# HELP jobs_total Jobs run.\n# TYPE jobs_total counter\njobs_total 5\n"
            "# HELP batch_size Items per batch.\n# TYPE batch_size histogram\n"
            'batch_size_bucket{le="10"} 1\nbatch_size_bucket{le="+Inf"} 2\nbatch_size_sum 44\nbatch_size_count 2\n',
        )


class TraceTest(unittest.TestCase):
    def setUp(self):
        self.tracer = Tracer(random.Random(42))

    def test_spans(self):
        """starts traces and child spans with W3C-sized ids"""
        root = self.tracer.start_span("GET /checkout", now=0)
        child = self.tracer.start_span("SELECT cart", now=1, parent=root)
        self.assertRegex(root.trace_id, r"^[0-9a-f]{32}$")
        self.assertRegex(root.span_id, r"^[0-9a-f]{16}$")
        self.assertIsNone(root.parent_id)
        self.assertEqual((child.trace_id, child.parent_id), (root.trace_id, root.span_id))
        self.assertNotEqual(child.span_id, root.span_id)
        self.assertEqual(self.tracer.spans, [root, child])
        other = self.tracer.start_span("GET /home", now=2)
        self.assertNotEqual(other.trace_id, root.trace_id, "no parent: a new trace")

    def test_propagation(self):
        """continues a trace across a network call via traceparent"""
        client = self.tracer.start_span("call payments", now=0)
        headers = inject(client, {"content-type": "application/json"})
        self.assertEqual(headers["traceparent"], f"00-{client.trace_id}-{client.span_id}-01")
        self.assertEqual(headers["content-type"], "application/json")

        payments = Tracer(random.Random(7))  # another service, another process
        server = payments.start_span("POST /charge", now=1, parent=extract(headers))
        self.assertEqual((server.trace_id, server.parent_id), (client.trace_id, client.span_id))

    def test_extract_rejects_garbage(self):
        """ignores missing or malformed traceparent headers"""
        good = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        self.assertEqual(extract({"traceparent": good}), SpanContext("4bf92f3577b34da6a3ce929d0e0e4736", "00f067aa0ba902b7"))
        for bad in (
            "",
            "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7",
            "00-4BF92F3577B34DA6A3CE929D0E0E4736-00f067aa0ba902b7-01",
            "00-4bf92f3577b34da6-00f067aa0ba902b7-01",
            "00-00000000000000000000000000000000-00f067aa0ba902b7-01",
            "00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01",
        ):
            self.assertIsNone(extract({"traceparent": bad}), bad)
        self.assertIsNone(extract({}))

    def test_critical_path(self):
        """follows the child that finished last at each level"""
        t = self.tracer
        root = t.start_span("GET /feed", now=0)
        auth = t.start_span("auth", now=1, parent=root)
        auth.finish(5)
        posts = t.start_span("load posts", now=5, parent=root)
        ads = t.start_span("load ads", now=5, parent=root)
        db = t.start_span("db query", now=6, parent=posts)
        db.finish(40)
        cache = t.start_span("cache get", now=6, parent=posts)
        cache.finish(8)
        posts.finish(42)
        ads.finish(30)
        root.finish(45)
        shuffled = t.spans[:]
        random.Random(1).shuffle(shuffled)
        self.assertEqual(critical_path(shuffled), ["GET /feed", "load posts", "db query"])

    def test_critical_path_from_a_remote_parent(self):
        """treats a span whose parent isn't in the set as the root"""
        parent = SpanContext("ab" * 16, "cd" * 8)
        server = self.tracer.start_span("POST /charge", now=0, parent=parent)
        fraud = self.tracer.start_span("fraud check", now=1, parent=server)
        fraud.finish(9)
        server.finish(10)
        self.assertEqual(critical_path(self.tracer.spans), ["POST /charge", "fraud check"])


class LogTest(unittest.TestCase):
    def test_structured_log(self):
        """writes JSON log lines that carry the trace context"""
        span = Tracer(random.Random(3)).start_span("GET /cart", now=0)
        line = solution.log_line("error", "payment declined", span, user_id=42, amount_cents=1999)
        self.assertNotIn("\n", line)
        record = json.loads(line)
        self.assertEqual(
            record,
            {"level": "error", "msg": "payment declined", "trace_id": span.trace_id, "span_id": span.span_id, "user_id": 42, "amount_cents": 1999},
        )
        self.assertEqual(list(record), sorted(record), "keys are sorted")
        self.assertEqual(json.loads(solution.log_line("info", "started")), {"level": "info", "msg": "started"})


class SLOTest(unittest.TestCase):
    def test_burn_rate(self):
        """measures how fast errors spend the error budget"""
        self.assertAlmostEqual(solution.burn_rate(1, 1000, 0.999), 1.0)
        self.assertAlmostEqual(solution.burn_rate(144, 10_000, 0.999), 14.4)
        self.assertAlmostEqual(solution.burn_rate(0, 500, 0.99), 0.0)
        self.assertEqual(solution.burn_rate(0, 0, 0.99), 0.0)

    def test_paging(self):
        """pages only when both windows burn fast"""
        slo = 0.999
        self.assertTrue(solution.should_page((150, 10_000), (2_000, 100_000), slo))
        self.assertFalse(solution.should_page((150, 10_000), (500, 100_000), slo), "a brief blip: the long window is fine")
        self.assertFalse(solution.should_page((5, 10_000), (2_000, 100_000), slo), "already recovered: the short window is fine")
        self.assertTrue(solution.should_page((70, 10_000), (700, 100_000), slo, threshold=6))


if __name__ == "__main__":
    unittest.main()
