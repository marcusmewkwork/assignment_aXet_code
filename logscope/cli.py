from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logscope",
        description="Streaming log-analysis CLI.",
    )
    subparsers = parser.add_subparsers(dest="command")

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("file")

    for command in ("timeline", "grep"):
        subparsers.add_parser(command)

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
        print(format_summary_text(summary))

    return 0
