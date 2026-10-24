from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys


def write_output(output: str) -> None:
    try:
        print(output)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(f"{output}\n".encode("utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logscope",
        description="Streaming log-analysis CLI.",
    )
    subparsers = parser.add_subparsers(dest="command")

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("file")

    timeline_parser = subparsers.add_parser("timeline")
    timeline_parser.add_argument("file")
    timeline_parser.add_argument("--bucket", default="15m")

    grep_parser = subparsers.add_parser("grep")
    grep_parser.add_argument("file")
    grep_parser.add_argument("--level")
    grep_parser.add_argument("--since")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "summary":
        from logscope.summary import format_summary_text, summarize

        try:
            summary = summarize(arguments.file)
        except OSError:
            print(f"Unable to read file: {arguments.file}", file=sys.stderr)
            return 1
        write_output(format_summary_text(summary))

    if arguments.command == "timeline":
        from logscope.timeline import build_timeline, format_timeline_text, parse_bucket

        try:
            bucket = parse_bucket(arguments.bucket)
        except ValueError as error:
            parser.error(str(error))
        try:
            timeline = build_timeline(arguments.file, bucket)
        except OSError:
            print(f"Unable to read file: {arguments.file}", file=sys.stderr)
            return 1
        write_output(format_timeline_text(timeline))

    if arguments.command == "grep":
        from logscope.grep import count_malformed_lines, iter_matches, parse_since, validate_level

        try:
            level = validate_level(arguments.level) if arguments.level else None
            since = parse_since(arguments.since) if arguments.since else None
        except ValueError as error:
            parser.error(str(error))
        try:
            for entry in iter_matches(arguments.file, level=level, since=since):
                print(entry.original_line, end="")
            malformed_lines = count_malformed_lines(arguments.file)
        except OSError:
            print(f"Unable to read file: {arguments.file}", file=sys.stderr)
            return 1
        print(f"Malformed lines: {malformed_lines}", file=sys.stderr)

    return 0
