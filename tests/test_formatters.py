import json

import pytest

from logscope.cli import main
from logscope.formatters import markdown_path


def test_summary_json_contains_expected_data(capsys):
    assert main(["summary", "tests/fixtures/summary.log", "--format", "json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert data["total_lines"] == 12
    assert data["levels"] == {"INFO": 1, "WARN": 1, "ERROR": 8}
    assert data["first_timestamp"] == "2026-10-01 08:00:00"


def test_timeline_json_contains_malformed_count(capsys):
    assert main(["timeline", "tests/fixtures/timeline.log", "--format", "json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert data["malformed_lines"] == 1
    assert data["buckets"][0] == {"timestamp": "2026-10-01 09:00:00", "count": 1}


def test_grep_json_is_valid_for_multiple_matches(capsys):
    assert main(["grep", "tests/fixtures/grep.log", "--level", "ERROR", "--format", "json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert data["malformed_lines"] == 1
    assert [match["message"] for match in data["matches"]][:2] == [
        "Before since",
        "At minute boundary",
    ]


def test_grep_json_is_valid_with_zero_matches(capsys):
    assert main(["grep", "tests/fixtures/grep.log", "--level", "INFO", "--since", "2026-10-01 10:00", "--format", "json"]) == 0

    assert json.loads(capsys.readouterr().out) == {"matches": [], "malformed_lines": 1}


def test_markdown_output_uses_explicit_path_and_overwrites(tmp_path, capsys):
    destination = tmp_path / "report.md"
    destination.write_text("old content", encoding="utf-8")

    assert main(["summary", "tests/fixtures/summary.log", "--format", "md", "--output", str(destination)]) == 0

    assert capsys.readouterr().out == f"{destination}\n"
    content = destination.read_text(encoding="utf-8")
    assert content.startswith("# Summary: summary.log\n")
    assert "| Malformed lines | 1 |" in content
    assert "old content" not in content


def test_timeline_and_grep_markdown_use_code_blocks(tmp_path, capsys):
    timeline_destination = tmp_path / "timeline.md"
    grep_destination = tmp_path / "grep.md"

    assert main(["timeline", "tests/fixtures/timeline.log", "--format", "md", "--output", str(timeline_destination)]) == 0
    assert main(["grep", "tests/fixtures/grep.log", "--format", "md", "--output", str(grep_destination)]) == 0

    capsys.readouterr()
    assert "```text" in timeline_destination.read_text(encoding="utf-8")
    grep_content = grep_destination.read_text(encoding="utf-8")
    assert "```text" in grep_content
    assert "2026-10-01 09:29:59 ERROR Before since" in grep_content


def test_default_markdown_path_includes_command_and_timestamp():
    path = markdown_path("summary", None)

    assert path.name.startswith("logscope-summary-")
    assert path.suffix == ".md"


@pytest.mark.parametrize("command", ["summary", "timeline", "grep"])
def test_output_is_rejected_for_non_markdown(command):
    with pytest.raises(SystemExit) as error:
        main([command, "tests/fixtures/summary.log", "--output", "report.md"])

    assert error.value.code == 2
