from datetime import datetime

import pytest

from logscope.parser import iter_entries, parse_line


def test_parse_line_parses_valid_entry_and_preserves_original_line():
    line = "2026-10-01 09:15:23 ERROR   Database unavailable  \n"

    entry = parse_line(line)

    assert entry is not None
    assert entry.timestamp == datetime(2026, 10, 1, 9, 15, 23)
    assert entry.level == "ERROR"
    assert entry.message == "Database unavailable"
    assert entry.original_line == line
    assert entry.line_number == 0


@pytest.mark.parametrize(
    "line",
    [
        "not a log line\n",
        "2026-13-01 09:15:23 INFO Invalid timestamp\n",
        "2026-10-01 09:15:23 DEBUG Unknown level\n",
        "2026-10-01 09:15:23 ERROR    \n",
        "    at com.shop.OrderController.create(OrderController.java:88)\n",
    ],
)
def test_parse_line_returns_none_for_malformed_input(line):
    assert parse_line(line) is None


def test_parse_line_normalizes_warning_to_warn():
    entry = parse_line("2026-10-01 09:15:23 WARNING Disk usage high\n")

    assert entry is not None
    assert entry.level == "WARN"


def test_iter_entries_streams_results_with_line_metadata(tmp_path):
    log_file = tmp_path / "mixed.log"
    log_file.write_bytes(
        b"2026-10-01 09:15:23 INFO Valid entry\n"
        b"\n"
        b"invalid\n"
        b"2026-10-01 09:15:24 ERROR Failed\n"
    )

    results = iter_entries(log_file)
    first = next(results)
    second = next(results)
    third = next(results)
    fourth = next(results)

    assert first.entry is not None
    assert first.entry.line_number == 1
    assert not first.is_blank
    assert second.entry is None
    assert second.is_blank
    assert third.entry is None
    assert not third.is_blank
    assert fourth.entry is not None
    assert fourth.entry.line_number == 4
    with pytest.raises(StopIteration):
        next(results)


def test_iter_entries_replaces_invalid_utf8_bytes(tmp_path):
    log_file = tmp_path / "invalid-utf8.log"
    log_file.write_bytes(b"2026-10-01 09:15:23 INFO valid \xff message\n")

    result = next(iter_entries(log_file))

    assert result.entry is not None
    assert result.entry.message == "valid \ufffd message"
