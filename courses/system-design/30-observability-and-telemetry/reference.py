"""Observability: Prometheus-style metrics, distributed traces, structured
logs, and SLO alerting."""

import json
import math
import re
from collections import namedtuple


def fmt(value):
    """Formats a number for the Prometheus text format."""
    if value == math.inf:
        return "+Inf"
    if float(value).is_integer():
        return str(int(value))
    return repr(float(value))


def _key(labels):
    """A label dict as sorted (name, value) pairs: one time series per distinct set."""
    return tuple(sorted(labels.items()))


def _labels(pairs):
    """(("method", "GET"), ("status", "200")) -> '{method="GET",status="200"}'"""
    if not pairs:
        return ""
    return "{" + ",".join(f'{k}="{v}"' for k, v in pairs) + "}"


# --- 1. Metrics ----------------------------------------------------------------


class Counter:
    def __init__(self, name, help):
        self.name, self.help = name, help
        self.values = {}  # sorted label pairs -> total

    def inc(self, amount=1, **labels):
        if amount < 0:
            raise ValueError("counters only go up")
        key = _key(labels)
        self.values[key] = self.values.get(key, 0) + amount

    def value(self, **labels):
        return self.values.get(_key(labels), 0)


class Histogram:
    def __init__(self, name, help, buckets):
        self.name, self.help = name, help
        self.bounds = sorted(buckets) + [math.inf]
        self.series = {}  # sorted label pairs -> {"counts": [...], "sum": s, "count": n}

    def observe(self, value, **labels):
        s = self.series.setdefault(_key(labels), {"counts": [0] * len(self.bounds), "sum": 0, "count": 0})
        i = next(i for i, bound in enumerate(self.bounds) if value <= bound)
        s["counts"][i] += 1
        s["sum"] += value
        s["count"] += 1

    def quantile(self, q, **labels):
        s = self.series.get(_key(labels))
        if not s or s["count"] == 0:
            return None
        rank = q * s["count"]
        seen = 0
        for i, n in enumerate(s["counts"]):
            if n and seen + n >= rank:
                upper = self.bounds[i]
                if upper == math.inf:
                    return self.bounds[-2]
                lower = self.bounds[i - 1] if i > 0 else 0
                return lower + (upper - lower) * (rank - seen) / n
            seen += n
        return self.bounds[-2]


def render(metrics):
    lines = []
    for m in metrics:
        kind = "counter" if isinstance(m, Counter) else "histogram"
        lines += [f"# HELP {m.name} {m.help}", f"# TYPE {m.name} {kind}"]
        if kind == "counter":
            for key in sorted(m.values):
                lines.append(f"{m.name}{_labels(key)} {fmt(m.values[key])}")
            continue
        for key in sorted(m.series):
            s = m.series[key]
            total = 0
            for bound, n in zip(m.bounds, s["counts"]):
                total += n
                lines.append(f"{m.name}_bucket{_labels(key + (('le', fmt(bound)),))} {total}")
            lines.append(f"{m.name}_sum{_labels(key)} {fmt(s['sum'])}")
            lines.append(f"{m.name}_count{_labels(key)} {s['count']}")
    return "\n".join(lines) + "\n"


# --- 2. Traces -----------------------------------------------------------------

SpanContext = namedtuple("SpanContext", "trace_id span_id")


class Span:
    def __init__(self, name, trace_id, span_id, parent_id, start):
        self.name = name
        self.trace_id, self.span_id, self.parent_id = trace_id, span_id, parent_id
        self.start, self.end = start, None

    def finish(self, now):
        self.end = now


class Tracer:
    def __init__(self, rng):
        self.rng = rng
        self.spans = []

    def new_id(self, hex_digits):
        return f"{self.rng.getrandbits(hex_digits * 4):0{hex_digits}x}"

    def start_span(self, name, now, parent=None):
        if parent is None:
            trace_id, parent_id = self.new_id(32), None
        else:
            trace_id, parent_id = parent.trace_id, parent.span_id
        span = Span(name, trace_id, self.new_id(16), parent_id, now)
        self.spans.append(span)
        return span


TRACEPARENT = re.compile(r"00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}")


def inject(span, headers):
    headers["traceparent"] = f"00-{span.trace_id}-{span.span_id}-01"
    return headers


def extract(headers):
    m = TRACEPARENT.fullmatch(headers.get("traceparent", ""))
    if not m or set(m.group(1)) == {"0"} or set(m.group(2)) == {"0"}:
        return None
    return SpanContext(m.group(1), m.group(2))


def critical_path(spans):
    ids = {s.span_id for s in spans}
    children = {}
    for s in spans:
        children.setdefault(s.parent_id, []).append(s)
    span = next(s for s in spans if s.parent_id not in ids)  # the root
    path = [span.name]
    while children.get(span.span_id):
        span = max(children[span.span_id], key=lambda c: c.end)
        path.append(span.name)
    return path


# --- 3. Logs -------------------------------------------------------------------


def log_line(level, message, span=None, **fields):
    record = {"level": level, "msg": message, **fields}
    if span is not None:
        record["trace_id"], record["span_id"] = span.trace_id, span.span_id
    return json.dumps(record, sort_keys=True)


# --- 4. SLOs -------------------------------------------------------------------


def burn_rate(errors, requests, slo):
    if requests == 0:
        return 0.0
    return (errors / requests) / (1 - slo)


def should_page(short_window, long_window, slo, threshold=14.4):
    return all(burn_rate(errors, requests, slo) >= threshold for errors, requests in (short_window, long_window))
