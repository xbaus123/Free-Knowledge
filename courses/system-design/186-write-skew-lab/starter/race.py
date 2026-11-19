"""Runs bookings at the same time, in the worst possible interleaving.
(Read-only: the tests use it, and so can you.)

Real races depend on luck. This helper removes the luck: every call
pauses right after its first SELECT until all the others have reached
theirs, so every check happens before any write. A call that's blocked
waiting for a lock can't reach the barrier, so the others go ahead after
a short timeout.
"""

import threading


def run_concurrently(db, calls, timeout=0.5):
    """Runs each zero-argument function in calls on its own thread and
    returns their results in order."""
    barrier = threading.Barrier(len(calls), timeout=timeout)
    paused = set()

    def pause(tx):
        me = threading.get_ident()
        if me in paused:
            return
        paused.add(me)
        try:
            barrier.wait()
        except threading.BrokenBarrierError:
            pass

    results, errors = [None] * len(calls), []

    def run(i):
        try:
            results[i] = calls[i]()
        except Exception as e:  # reported below
            errors.append(e)

    db.after_select = pause
    try:
        threads = [threading.Thread(target=run, args=(i,)) for i in range(len(calls))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        db.after_select = None
    if errors:
        raise errors[0]
    return results
