"""Where the store keeps its files. (Read-only.)

A data directory holds log segments and at most one SSTable:

    segment-000001.log   segment-000004.log   sstable-000003.sst

Every file gets a new, higher id when it's created.
"""

import os
import re

_NAME = re.compile(r"^(segment|sstable)-(\d{6})\.(log|sst)$")


def segment_path(directory, file_id):
    return os.path.join(directory, f"segment-{file_id:06d}.log")


def sstable_path(directory, file_id):
    return os.path.join(directory, f"sstable-{file_id:06d}.sst")


def file_ids(directory):
    """([segment ids], [sstable ids]), each sorted oldest first."""
    segments, sstables = [], []
    for name in os.listdir(directory):
        m = _NAME.match(name)
        if m:
            (segments if m.group(1) == "segment" else sstables).append(int(m.group(2)))
    return sorted(segments), sorted(sstables)
