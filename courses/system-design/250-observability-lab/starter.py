"""Observability: Prometheus-style metrics, distributed traces, structured
logs, and SLO alerting.

Four independent parts. Counter, the formatting helpers, Span, and
Tracer.new_id are provided.
"""

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
    """Counts observations into buckets. buckets: the upper bounds, such as
    [0.1, 0.25, 0.5, 1]; an implicit +Inf bucket catches everything else."""

    def __init__(self, name, help, buckets):
        self.name, self.help = name, help
        self.bounds = sorted(buckets) + [math.inf]

    def observe(self, value, **labels):
        """Count value in the first bucket whose bound is >= value."""
        raise NotImplementedError

    def quantile(self, q, **labels):
        """Estimate the q-quantile (0.99 for p99) from the buckets, like
        Prometheus's histogram_quantile. None if nothing was observed."""
        raise NotImplementedError


def render(metrics):
    """The Prometheus text exposition format for a list of Counters and
    Histograms, ending with a newline."""
    raise NotImplementedError


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
        self.spans = []  # every span started, in order

    def new_id(self, hex_digits):
        """A random id of hex_digits lowercase hex digits."""
        return f"{self.rng.getrandbits(hex_digits * 4):0{hex_digits}x}"

    def start_span(self, name, now, parent=None):
        """Start a span. parent: a Span or a SpanContext, or None for a new trace."""
        raise NotImplementedError


def inject(span, headers):
    """Add the W3C traceparent header for span to headers. Return headers."""
    raise NotImplementedError


def extract(headers):
    """The SpanContext in a valid traceparent header, or None."""
    raise NotImplementedError


def critical_path(spans):
    """The names along the critical path of one trace's finished spans:
    from the root, repeatedly step to the child that finished last."""
    raise NotImplementedError


# --- 3. Logs -------------------------------------------------------------------


def log_line(level, message, span=None, **fields):
    """One structured log line: a JSON object with sorted keys."""
    raise NotImplementedError


# --- 4. SLOs -------------------------------------------------------------------


def burn_rate(errors, requests, slo):
    """How fast errors are spending the error budget (1.0: exactly on budget)."""
    raise NotImplementedError


def should_page(short_window, long_window, slo, threshold=14.4):
    """Page only if both windows, each (errors, requests), burn at threshold or faster."""
    raise NotImplementedError
