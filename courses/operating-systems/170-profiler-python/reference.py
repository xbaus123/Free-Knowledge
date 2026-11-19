"""Two performance tools: a sampling profiler and DTrace-style on-CPU accounting."""

import bisect


def function_at(symbols, address):
    starts = [start for start, _ in symbols]
    i = bisect.bisect_right(starts, address) - 1
    if i < 0:
        return None
    return symbols[i][1]


def profile(samples, symbols):
    counts = {}
    for address in samples:
        name = function_at(symbols, address) or "?"
        counts[name] = counts.get(name, 0) + 1
    return counts


def hottest(samples, symbols, n):
    counts = profile(samples, symbols)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    return [(name, round(100 * c / len(samples), 1)) for name, c in ranked]


def cpu_time(events, uid=None):
    started = {}
    totals = {}
    for ts, kind, program, user in events:
        if uid is not None and user != uid:
            continue
        if kind == "on":
            started[program] = ts
        elif kind == "off" and program in started:
            totals[program] = totals.get(program, 0) + ts - started.pop(program)
    return totals
