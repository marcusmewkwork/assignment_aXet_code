from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys
from typing import TextIO

from logscope.parser import LogEntry
from logscope.summary import Summary
from logscope.timeline import Timeline, format_timeline_text


def timestamp_value(value: datetime | None) -> str | None:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value is not None else None


def summary_data(summary: Summary) -> dict[str, object]:
    return {
        "total_lines": summary.total_lines,
        "parsed_lines": summary.parsed_lines,
        "malformed_lines": summary.malformed_lines,
        "levels": summary.level_counts,
        "top_errors": [
            {"message": error.message, "count": error.count}
            for error in summary.top_errors
        ],
        "first_timestamp": timestamp_value(summary.first_timestamp),
        "last_timestamp": timestamp_value(summary.last_timestamp),
    }


def timeline_data(timeline: Timeline) -> dict[str, object]:
    return {
        "malformed_lines": timeline.malformed_lines,
        "buckets": [
            {"timestamp": timestamp_value(bucket_start), "count": count}
            for bucket_start, count in timeline.buckets
        ],
    }


def write_json(data: dict[str, object], stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    json.dump(data, target)
    target.write("\n")


def write_grep_json(
    entries: object, malformed_lines: int, stream: TextIO | None = None
) -> None:
    target = stream or sys.stdout
    target.write('{"matches":[')
    first = True
    for entry in entries:
        if not first:
            target.write(",")
        json.dump(entry_data(entry), target)
        first = False
    target.write(f'],"malformed_lines":{malformed_lines}}}\n')


def entry_data(entry: LogEntry) -> dict[str, object]:
    return {
        "line_number": entry.line_number,
        "timestamp": timestamp_value(entry.timestamp),
        "level": entry.level,
        "message": entry.message,
    }


def markdown_path(command: str, output: str | None, now: datetime | None = None) -> Path:
    if output is not None:
        return Path(output)
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    return Path(f"logscope-{command}-{timestamp}.md")


def write_summary_markdown(summary: Summary, file_name: str, destination: Path) -> None:
    data = summary_data(summary)
    lines = [
        f"# Summary: {file_name}",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total lines | {data['total_lines']} |",
        f"| Lines parsed | {data['parsed_lines']} |",
        f"| Malformed lines | {data['malformed_lines']} |",
        f"| First timestamp | {data['first_timestamp'] or 'n/a'} |",
        f"| Last timestamp | {data['last_timestamp'] or 'n/a'} |",
        "",
        "## Levels",
        "",
        "| Level | Count |",
        "|---|---:|",
        *(f"| {level} | {count} |" for level, count in summary.level_counts.items()),
        "",
        "## Top 5 errors",
        "",
        "| Message | Count |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {error.message} | {error.count} |" for error in summary.top_errors
    )
    if not summary.top_errors:
        lines.append("| n/a | 0 |")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_timeline_markdown(timeline: Timeline, file_name: str, destination: Path) -> None:
    destination.write_text(
        f"# Timeline: {file_name}\n\nMalformed lines: {timeline.malformed_lines}\n\n```text\n"
        f"{format_timeline_text(timeline)}\n```\n",
        encoding="utf-8",
    )


def write_grep_markdown(
    entries: object, malformed_lines: int, file_name: str, destination: Path
) -> None:
    with destination.open("w", encoding="utf-8") as report:
        report.write(f"# Grep: {file_name}\n\n```text\n")
        for entry in entries:
            report.write(entry.original_line)
        report.write(f"```\n\nMalformed lines: {malformed_lines}\n")
