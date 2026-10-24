from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterator

from logscope.parser import LogEntry, iter_entries


_LEVELS = frozenset({"INFO", "WARN", "ERROR"})
_SINCE_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")


def parse_since(value: str) -> datetime:
    for timestamp_format in _SINCE_FORMATS:
        try:
            return datetime.strptime(value, timestamp_format)
        except ValueError:
            continue
    raise ValueError("since must use YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS")


def validate_level(value: str) -> str:
    level = value.upper()
    if level not in _LEVELS:
        raise ValueError("level must be INFO, WARN, or ERROR")
    return level


def entry_matches(
    entry: LogEntry, level: str | None = None, since: datetime | None = None
) -> bool:
    return (level is None or entry.level == level) and (
        since is None or entry.timestamp >= since
    )


def iter_matches(
    file_path: str | Path, level: str | None = None, since: datetime | None = None
) -> Iterator[LogEntry]:
    for result in iter_entries(file_path):
        if result.entry is not None and entry_matches(result.entry, level, since):
            yield result.entry


def count_malformed_lines(file_path: str | Path) -> int:
    return sum(
        1
        for result in iter_entries(file_path)
        if not result.is_blank and result.entry is None
    )
