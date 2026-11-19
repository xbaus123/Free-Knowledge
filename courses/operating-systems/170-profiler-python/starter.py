"""Two performance tools: a sampling profiler and DTrace-style on-CPU accounting."""

import bisect


def function_at(symbols, address):
    """symbols: a list of (start_address, function_name), sorted by start.
    Each function runs from its start up to (not including) the next start;
    the last one runs forever. Return the name of the function containing
    address, or None if address is below the first start."""
    # TODO
    pass


def profile(samples, symbols):
    """samples: instruction-pointer values, one per timer tick.
    Return {function name: number of samples in it}. Samples that land in
    no function are counted under "?"."""
    # TODO
    pass


def hottest(samples, symbols, n):
    """The n functions with the most samples, as (name, percent) pairs,
    most samples first. percent = 100 * count / len(samples), rounded to
    one decimal place. Break ties by name (alphabetical)."""
    # TODO
    pass


def cpu_time(events, uid=None):
    """events: (timestamp, "on" or "off", program, user_id) tuples in time order.
    Like the sched.d script: when a program goes "on" the CPU, remember the
    time; when it goes "off", add the elapsed time to that program's total.
    Ignore an "off" with no matching "on". If uid is given, only count
    events for that user. Return {program: total time}."""
    # TODO
    pass


if __name__ == "__main__":
    symbols = [(0x1000, "main"), (0x1400, "parse"), (0x2000, "draw")]
    samples = [0x1004, 0x1500, 0x1510, 0x2100, 0x1520, 0x0500]
    print(function_at(symbols, 0x1500))     # parse
    print(profile(samples, symbols))        # {'main': 1, 'parse': 3, 'draw': 1, '?': 1}
    print(hottest(samples, symbols, 2))     # [('parse', 50.0), ('?', 16.7)]

    events = [(0, "on", "java", 101), (40, "off", "java", 101),
              (40, "on", "Xorg", 0), (55, "off", "Xorg", 0),
              (55, "on", "java", 101), (60, "off", "java", 101)]
    print(cpu_time(events))                 # {'java': 45, 'Xorg': 15}
    print(cpu_time(events, uid=101))        # {'java': 45}
