from datetime import datetime

import pytest

from logscope.cli import main
from logscope.summary import format_summary_text, summarize


def test_summarize_collects_counts_timestamps_and_top_errors():
    summary = summarize("tests/fixtures/summary.log")

    assert summary.total_lines == 12
    assert summary.parsed_lines == 10
    assert summary.malformed_lines == 1
    assert summary.level_counts == {"INFO": 1, "WARN": 1, "ERROR": 8}
    assert summary.first_timestamp == datetime(2026, 10, 1, 8, 0)
    assert summary.last_timestamp == datetime(2026, 10, 1, 10, 0)
    assert [(error.message, error.count) for error in summary.top_errors] == [
        ("Alpha failure", 2),
        ("Zebra failure", 2),
        ("Bravo failure", 1),
        ("Delta failure", 1),
        ("Echo failure", 1),
    ]


def test_summarize_empty_file_has_zero_counts_and_no_timestamps(tmp_path):
    log_file = tmp_path / "empty.log"
    log_file.write_text("")

    summary = summarize(log_file)

    assert summary.total_lines == 0
    assert summary.parsed_lines == 0
    assert summary.malformed_lines == 0
    assert summary.level_counts == {"INFO": 0, "WARN": 0, "ERROR": 0}
    assert summary.top_errors == ()
    assert summary.first_timestamp is None
    assert summary.last_timestamp is None
    assert "First timestamp: n/a" in format_summary_text(summary)
    assert "Last timestamp: n/a" in format_summary_text(summary)


def test_summarize_all_malformed_file_has_zero_parsed_entries(tmp_path):
    log_file = tmp_path / "malformed.log"
    log_file.write_text("not a log\n2026-10-01 09:00:00 ERROR   \n")

    summary = summarize(log_file)

    assert summary.total_lines == 2
    assert summary.parsed_lines == 0
    assert summary.malformed_lines == 2
    assert summary.level_counts == {"INFO": 0, "WARN": 0, "ERROR": 0}
    assert summary.first_timestamp is None
    assert summary.last_timestamp is None


def test_summary_command_prints_text_output(capsys):
    assert main(["summary", "tests/fixtures/summary.log"]) == 0

    output = capsys.readouterr().out
    assert "Total lines: 12" in output
    assert "Malformed lines: 1" in output
    assert "2 Alpha failure" in output


def test_summary_command_returns_one_for_missing_file(capsys):
    assert main(["summary", "missing.log"]) == 1

    assert "Unable to read file: missing.log" in capsys.readouterr().err


def test_summary_format_is_rejected_until_step_six():
    with pytest.raises(SystemExit) as error:
        main(["summary", "tests/fixtures/summary.log", "--format", "json"])

    assert error.value.code == 2
