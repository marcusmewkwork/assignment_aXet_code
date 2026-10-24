from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
import re
from typing import Iterator


_LINE_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>INFO|WARN|WARNING|ERROR)\b(?P<message>.*)$"
)
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class LogEntry:
    timestamp: datetime
    level: str
    message: str
    original_line: str
    line_number: int = 0


@dataclass(frozen=True)
class ParsedLine:
    line_number: int
    entry: LogEntry | None
    is_blank: bool


def parse_line(line: str) -> LogEntry | None:
    match = _LINE_PATTERN.match(line.rstrip("\r\n"))
    if match is None:
        return None

    try:
        timestamp = datetime.strptime(match.group("timestamp"), _TIMESTAMP_FORMAT)
    except ValueError:
        return None

    message = match.group("message").strip()
    if not message:
        return None

    level = match.group("level")
    if level == "WARNING":
        level = "WARN"

    return LogEntry(
        timestamp=timestamp,
        level=level,
        message=message,
        original_line=line,
    )


def iter_entries(file_path: str | Path) -> Iterator[ParsedLine]:
    with Path(file_path).open("r", encoding="utf-8", errors="replace") as log_file:
        for line_number, line in enumerate(log_file, start=1):
            if not line.strip():
                yield ParsedLine(line_number=line_number, entry=None, is_blank=True)
                continue

            entry = parse_line(line)
            if entry is not None:
                entry = replace(entry, line_number=line_number)
            yield ParsedLine(line_number=line_number, entry=entry, is_blank=False)
