from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from logscope.parser import iter_entries


@dataclass(frozen=True)
class ErrorMessageCount:
    message: str
    count: int


@dataclass(frozen=True)
class Summary:
    total_lines: int
    parsed_lines: int
    malformed_lines: int
    level_counts: dict[str, int]
    top_errors: tuple[ErrorMessageCount, ...]
    first_timestamp: datetime | None
    last_timestamp: datetime | None


def summarize(file_path: str | Path) -> Summary:
    total_lines = 0
    parsed_lines = 0
    malformed_lines = 0
    level_counts = {"INFO": 0, "WARN": 0, "ERROR": 0}
    error_messages: Counter[str] = Counter()
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None

    for result in iter_entries(file_path):
        total_lines += 1
        if result.is_blank:
            continue
        if result.entry is None:
            malformed_lines += 1
            continue

        entry = result.entry
        parsed_lines += 1
        level_counts[entry.level] += 1
        if entry.level == "ERROR":
            error_messages[entry.message] += 1
        if first_timestamp is None or entry.timestamp < first_timestamp:
            first_timestamp = entry.timestamp
        if last_timestamp is None or entry.timestamp > last_timestamp:
            last_timestamp = entry.timestamp

    top_errors = tuple(
        ErrorMessageCount(message=message, count=count)
        for message, count in sorted(
            error_messages.items(), key=lambda item: (-item[1], item[0])
        )[:5]
    )

    return Summary(
        total_lines=total_lines,
        parsed_lines=parsed_lines,
        malformed_lines=malformed_lines,
        level_counts=level_counts,
        top_errors=top_errors,
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
    )


def format_summary_text(summary: Summary) -> str:
    first_timestamp = (
        summary.first_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if summary.first_timestamp is not None
        else "n/a"
    )
    last_timestamp = (
        summary.last_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if summary.last_timestamp is not None
        else "n/a"
    )
    lines = [
        f"Total lines: {summary.total_lines}",
        f"Lines parsed: {summary.parsed_lines}",
        f"Malformed lines: {summary.malformed_lines}",
        "Levels:",
        f"  INFO: {summary.level_counts['INFO']}",
        f"  WARN: {summary.level_counts['WARN']}",
        f"  ERROR: {summary.level_counts['ERROR']}",
        f"First timestamp: {first_timestamp}",
        f"Last timestamp: {last_timestamp}",
        "Top 5 errors:",
    ]
    if summary.top_errors:
        lines.extend(
            f"  {error.count} {error.message}" for error in summary.top_errors
        )
    else:
        lines.append("  n/a")
    return "\n".join(lines)
