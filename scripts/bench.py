from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import time

import psutil


@dataclass(frozen=True)
class BenchmarkResult:
    command: str
    duration_seconds: float
    peak_rss_bytes: int
    exit_code: int


def benchmark_command(log_file: str | Path, command: str) -> BenchmarkResult:
    arguments = [sys.executable, "-m", "logscope", command, str(log_file)]
    process = subprocess.Popen(
        arguments,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    monitored_process = psutil.Process(process.pid)
    peak_rss_bytes = 0
    started_at = time.perf_counter()

    while process.poll() is None:
        try:
            peak_rss_bytes = max(peak_rss_bytes, monitored_process.memory_info().rss)
        except psutil.NoSuchProcess:
            break
        time.sleep(0.01)

    try:
        peak_rss_bytes = max(peak_rss_bytes, monitored_process.memory_info().rss)
    except psutil.NoSuchProcess:
        pass

    return BenchmarkResult(
        command=command,
        duration_seconds=time.perf_counter() - started_at,
        peak_rss_bytes=peak_rss_bytes,
        exit_code=process.wait(),
    )


def benchmark(log_file: str | Path) -> tuple[int, tuple[BenchmarkResult, ...]]:
    path = Path(log_file)
    input_size = path.stat().st_size
    results = tuple(
        benchmark_command(path, command) for command in ("summary", "timeline", "grep")
    )
    return input_size, results


def format_results(input_size: int, results: tuple[BenchmarkResult, ...]) -> str:
    lines = [f"Input size: {input_size} bytes"]
    for result in results:
        lines.append(
            f"{result.command}: {result.duration_seconds:.3f}s | "
            f"peak RSS: {result.peak_rss_bytes} bytes | exit: {result.exit_code}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark logscope commands.")
    parser.add_argument("file")
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    try:
        input_size, results = benchmark(arguments.file)
    except OSError:
        print(f"Unable to read file: {arguments.file}", file=sys.stderr)
        return 1
    print(format_results(input_size, results))
    return 0 if all(result.exit_code == 0 for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
