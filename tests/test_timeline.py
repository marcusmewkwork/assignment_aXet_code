from datetime import datetime, timedelta

import pytest

from logscope.cli import main
from logscope.timeline import build_timeline, floor_to_bucket, format_timeline_text, parse_bucket


def test_parse_bucket_accepts_positive_minutes_and_hours():
    assert parse_bucket("5m") == timedelta(minutes=5)
    assert parse_bucket("1h") == timedelta(hours=1)


@pytest.mark.parametrize("value", ["0m", "0h", "15", "15s", "-1m", "1.5h"])
def test_parse_bucket_rejects_invalid_values(value):
    with pytest.raises(ValueError, match="bucket must be"):
        parse_bucket(value)


def test_floor_to_bucket_aligns_to_clock_boundaries():
    timestamp = datetime(2026, 10, 1, 9, 29, 59)

    assert floor_to_bucket(timestamp, timedelta(minutes=15)) == datetime(2026, 10, 1, 9, 15)
    assert floor_to_bucket(timestamp, timedelta(hours=1)) == datetime(2026, 10, 1, 9, 0)


def test_build_timeline_counts_errors_and_fills_empty_buckets():
    timeline = build_timeline("tests/fixtures/timeline.log", timedelta(minutes=15))

    assert timeline.malformed_lines == 1
    assert timeline.buckets == (
        (datetime(2026, 10, 1, 9, 0), 1),
        (datetime(2026, 10, 1, 9, 15), 1),
        (datetime(2026, 10, 1, 9, 30), 1),
        (datetime(2026, 10, 1, 9, 45), 1),
    )


def test_build_timeline_handles_no_errors_and_malformed_input(tmp_path):
    log_file = tmp_path / "no-errors.log"
    log_file.write_text("not a log\n\n2026-10-01 09:00:00 INFO Healthy\n")

    timeline = build_timeline(log_file, timedelta(minutes=15))

    assert timeline.malformed_lines == 1
    assert timeline.buckets == ()
    assert format_timeline_text(timeline) == "Malformed lines: 1\nNo errors found."


def test_timeline_command_uses_default_bucket_and_text_output(capsys):
    assert main(["timeline", "tests/fixtures/timeline.log"]) == 0

    output = capsys.readouterr().out
    assert "Malformed lines: 1" in output
    assert "2026-10-01 09:00 |" in output
    assert "2026-10-01 09:45 |" in output


def test_timeline_command_rejects_invalid_bucket():
    with pytest.raises(SystemExit) as error:
        main(["timeline", "tests/fixtures/timeline.log", "--bucket", "15s"])

    assert error.value.code == 2


def test_timeline_command_returns_one_for_missing_file(capsys):
    assert main(["timeline", "missing.log"]) == 1

    assert "Unable to read file: missing.log" in capsys.readouterr().err
