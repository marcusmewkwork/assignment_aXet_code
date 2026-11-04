from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys

import pytest

from logscope.cli import main
from logscope.grep import entry_matches, iter_matches, parse_since, validate_level
from logscope.parser import parse_line


def test_parse_since_accepts_minute_and_second_precision():
    assert parse_since("2026-10-01 09:30") == datetime(2026, 10, 1, 9, 30)
    assert parse_since("2026-10-01 09:30:10") == datetime(2026, 10, 1, 9, 30, 10)


@pytest.mark.parametrize("value", ["2026-10-01", "2026/10/01 09:30", "not a date"])
def test_parse_since_rejects_invalid_values(value):
    with pytest.raises(ValueError, match="since must use"):
        parse_since(value)


@pytest.mark.parametrize("value", ["info", "WARN", "ERROR"])
def test_validate_level_accepts_supported_levels(value):
    assert validate_level(value) == value.upper()


def test_validate_level_rejects_unknown_level():
    with pytest.raises(ValueError, match="level must be"):
        validate_level("DEBUG")


def test_entry_matches_combines_filters_with_and():
    entry = parse_line("2026-10-01 09:30:00 ERROR Database unavailable\n")

    assert entry is not None
    assert entry_matches(entry, "ERROR", datetime(2026, 10, 1, 9, 30))
    assert not entry_matches(entry, "INFO", datetime(2026, 10, 1, 9, 30))
    assert not entry_matches(entry, "ERROR", datetime(2026, 10, 1, 9, 30, 1))


def test_iter_matches_streams_unfiltered_and_filtered_entries():
    unfiltered = iter_matches("tests/fixtures/grep.log")
    assert next(unfiltered).message == "Before since"

    filtered = iter_matches(
        "tests/fixtures/grep.log",
        level="ERROR",
        since=datetime(2026, 10, 1, 9, 30),
    )
    assert [entry.message for entry in filtered] == [
        "At minute boundary",
        "At second boundary",
        "Later error",
    ]


def test_grep_command_prints_original_lines_and_malformed_count(capsys):
    assert main(["grep", "tests/fixtures/grep.log", "--level", "ERROR", "--since", "2026-10-01 09:30"]) == 0

    captured = capsys.readouterr()
    assert captured.out == (
        "2026-10-01 09:30:00 ERROR At minute boundary\n"
        "2026-10-01 09:30:10 ERROR At second boundary\n"
        "2026-10-01 09:31:00 ERROR Later error\n"
    )
    assert captured.err == "Malformed lines: 1\n"


def test_grep_handles_invalid_utf8_with_cp1252_stdout(tmp_path):
    fixture = tmp_path / "invalid-utf8.log"
    fixture.write_bytes(b"2026-10-01 09:00:00 ERROR bad bytes \xff\xfe\n")
    environment = {**os.environ, "PYTHONIOENCODING": "cp1252"}

    result = subprocess.run(
        [sys.executable, "-m", "logscope", "grep", str(fixture)],
        capture_output=True,
        cwd=Path(__file__).parents[1],
        env=environment,
    )

    assert result.returncode == 0
    assert b"Traceback" not in result.stderr


def test_grep_command_handles_empty_and_all_malformed_files(tmp_path, capsys):
    empty_file = tmp_path / "empty.log"
    empty_file.write_text("")
    malformed_file = tmp_path / "malformed.log"
    malformed_file.write_text("bad\n\n2026-10-01 09:00:00 INFO  \n")

    assert main(["grep", str(empty_file)]) == 0
    assert capsys.readouterr().err == "Malformed lines: 0\n"
    assert main(["grep", str(malformed_file)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Malformed lines: 2\n"


def test_grep_command_rejects_invalid_filters():
    with pytest.raises(SystemExit) as invalid_level:
        main(["grep", "tests/fixtures/grep.log", "--level", "DEBUG"])
    assert invalid_level.value.code == 2

    with pytest.raises(SystemExit) as invalid_since:
        main(["grep", "tests/fixtures/grep.log", "--since", "invalid"])
    assert invalid_since.value.code == 2


def test_grep_command_returns_one_for_missing_file(capsys):
    assert main(["grep", "missing.log"]) == 1

    assert "Unable to read file: missing.log" in capsys.readouterr().err
