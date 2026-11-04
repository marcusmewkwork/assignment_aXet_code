from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from logscope.formatters import (
    markdown_path,
    summary_data,
    timeline_data,
    write_grep_json,
    write_grep_markdown,
    write_json,
    write_summary_markdown,
    write_timeline_markdown,
)
from logscope.grep import count_malformed_lines, iter_matches, parse_since, validate_level
from logscope.summary import format_summary_text, summarize
from logscope.timeline import build_timeline, format_timeline_text, parse_bucket


def write_output(output: str) -> None:
    try:
        print(output)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(f"{output}\n".encode("utf-8"))


def add_output_arguments(command_parser: argparse.ArgumentParser) -> None:
    command_parser.add_argument("--format", choices=("text", "json", "md"), default="text")
    command_parser.add_argument("--output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logscope",
        description="Streaming log-analysis CLI.",
    )
    subparsers = parser.add_subparsers(dest="command")

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("file")
    add_output_arguments(summary_parser)

    timeline_parser = subparsers.add_parser("timeline")
    timeline_parser.add_argument("file")
    timeline_parser.add_argument("--bucket", default="15m")
    add_output_arguments(timeline_parser)

    grep_parser = subparsers.add_parser("grep")
    grep_parser.add_argument("file")
    grep_parser.add_argument("--level")
    grep_parser.add_argument("--since")
    add_output_arguments(grep_parser)

    return parser


def validate_output_arguments(parser: argparse.ArgumentParser, arguments: argparse.Namespace) -> None:
    if arguments.output and arguments.format != "md":
        parser.error("--output is only allowed with --format md")


def write_markdown_path(path: Path) -> None:
    print(path)


def main(argv: Sequence[str] | None = None) -> int:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.command is None:
        parser.print_help()
        return 0
    validate_output_arguments(parser, arguments)

    try:
        if arguments.command == "summary":
            summary = summarize(arguments.file)
            if arguments.format == "text":
                write_output(format_summary_text(summary))
            elif arguments.format == "json":
                write_json(summary_data(summary))
            else:
                destination = markdown_path("summary", arguments.output)
                write_summary_markdown(summary, Path(arguments.file).name, destination)
                write_markdown_path(destination)

        elif arguments.command == "timeline":
            try:
                bucket = parse_bucket(arguments.bucket)
            except ValueError as error:
                parser.error(str(error))
            timeline = build_timeline(arguments.file, bucket)
            if arguments.format == "text":
                write_output(format_timeline_text(timeline))
            elif arguments.format == "json":
                write_json(timeline_data(timeline))
            else:
                destination = markdown_path("timeline", arguments.output)
                write_timeline_markdown(timeline, Path(arguments.file).name, destination)
                write_markdown_path(destination)

        elif arguments.command == "grep":
            try:
                level = validate_level(arguments.level) if arguments.level else None
                since = parse_since(arguments.since) if arguments.since else None
            except ValueError as error:
                parser.error(str(error))
            malformed_lines = count_malformed_lines(arguments.file)
            entries = iter_matches(arguments.file, level=level, since=since)
            if arguments.format == "text":
                for entry in entries:
                    print(entry.original_line, end="")
                print(f"Malformed lines: {malformed_lines}", file=sys.stderr)
            elif arguments.format == "json":
                write_grep_json(entries, malformed_lines)
            else:
                destination = markdown_path("grep", arguments.output)
                write_grep_markdown(entries, malformed_lines, Path(arguments.file).name, destination)
                write_markdown_path(destination)
    except OSError:
        print(f"Unable to read file: {arguments.file}", file=sys.stderr)
        return 1

    return 0
