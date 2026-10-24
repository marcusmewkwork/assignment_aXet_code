from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import re

from logscope.parser import iter_entries


_BUCKET_PATTERN = re.compile(r"^(?P<value>[1-9]\d*)(?P<unit>[mh])$")


@dataclass(frozen=True)
class Timeline:
    bucket: timedelta
    malformed_lines: int
    buckets: tuple[tuple[datetime, int], ...]


def parse_bucket(value: str) -> timedelta:
    match = _BUCKET_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("bucket must be a positive value ending in 'm' or 'h'")

    amount = int(match.group("value"))
    if match.group("unit") == "m":
        return timedelta(minutes=amount)
    return timedelta(hours=amount)


def floor_to_bucket(timestamp: datetime, bucket: timedelta) -> datetime:
    bucket_seconds = int(bucket.total_seconds())
    day_start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_seconds = int((timestamp - day_start).total_seconds())
    return day_start + timedelta(seconds=elapsed_seconds - elapsed_seconds % bucket_seconds)


def build_timeline(file_path: str | Path, bucket: timedelta) -> Timeline:
    counts: Counter[datetime] = Counter()
    malformed_lines = 0
    first_bucket: datetime | None = None
    last_bucket: datetime | None = None

    for result in iter_entries(file_path):
        if result.is_blank:
            continue
        if result.entry is None:
            malformed_lines += 1
            continue
        if result.entry.level != "ERROR":
            continue

        bucket_start = floor_to_bucket(result.entry.timestamp, bucket)
        counts[bucket_start] += 1
        if first_bucket is None or bucket_start < first_bucket:
            first_bucket = bucket_start
        if last_bucket is None or bucket_start > last_bucket:
            last_bucket = bucket_start

    if first_bucket is None or last_bucket is None:
        return Timeline(bucket=bucket, malformed_lines=malformed_lines, buckets=())

    buckets: list[tuple[datetime, int]] = []
    current_bucket = first_bucket
    while current_bucket <= last_bucket:
        buckets.append((current_bucket, counts[current_bucket]))
        current_bucket += bucket

    return Timeline(
        bucket=bucket,
        malformed_lines=malformed_lines,
        buckets=tuple(buckets),
    )


def format_timeline_text(timeline: Timeline) -> str:
    lines = [f"Malformed lines: {timeline.malformed_lines}"]
    if not timeline.buckets:
        lines.append("No errors found.")
        return "\n".join(lines)

    maximum_count = max(count for _, count in timeline.buckets)
    for bucket_start, count in timeline.buckets:
        bar_length = 0 if count == 0 else max(1, round(count * 50 / maximum_count))
        lines.append(
            f"{bucket_start.strftime('%Y-%m-%d %H:%M')} | {'█' * bar_length} {count}"
        )
    return "\n".join(lines)
