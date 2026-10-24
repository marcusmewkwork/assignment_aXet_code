from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import random


_SEED = 20261001
_START_TIMESTAMP = datetime(2026, 10, 1, 9, 0, 0)
_LEVEL_WEIGHTS = (75, 15, 8, 2)
_INFO_MESSAGES = (
    "User login successful",
    "Cache refreshed",
    "Session closed",
    "Scheduled job started",
    "Scheduled job finished",
    "Order created",
    "Health check OK",
    "Request completed in 120ms",
    "Payment processed",
)
_WARN_MESSAGES = (
    "Slow query detected (>2s)",
    "Disk usage above 80%",
    "Retrying request to inventory-service",
    "High memory usage on worker-2",
    "Deprecated API endpoint called",
    "Connection pool nearing capacity",
    "Background job exceeded expected duration",
    "Response queue depth increasing",
    "Cache eviction rate elevated",
)
_ERROR_MESSAGES = (
    "Database connection timeout after 30s",
    "Failed to connect to inventory-service",
    "Payment gateway returned 503",
    "NullPointerException in OrderController",
    "Redis connection refused",
    "Disk write failed: No space left on device",
    "Authentication token validation failed",
    "Order fulfillment request timed out",
    "Unable to publish event to message queue",
)
_MALFORMED_LINES = (
    "this line is complete garbage\n",
    "2026-13-45 99:99:99 ERROR Impossible timestamp\n",
    "2026/10/01 09:00:00 INFO Wrong date separators\n",
    "2026-10-01 09:00:00 DEBUG Unknown level\n",
    "2026-10-01 09:00:00 ERROR\n",
    "    at com.shop.OrderController.create(OrderController.java:88)\n",
)


def generate_log(size_mb: float, output_path: str | Path) -> int:
    if size_mb <= 0:
        raise ValueError("size_mb must be greater than zero")

    target_bytes = int(size_mb * 1024 * 1024)
    bytes_written = 0
    timestamp = _START_TIMESTAMP
    generator = random.Random(_SEED)
    destination = Path(output_path)

    with destination.open("wb") as log_file:
        while bytes_written < target_bytes:
            timestamp += timedelta(seconds=generator.randint(0, 3))
            line = generate_line(generator, timestamp)
            encoded_line = line.encode("utf-8")
            log_file.write(encoded_line)
            bytes_written += len(encoded_line)

    return bytes_written


def generate_line(generator: random.Random, timestamp: datetime) -> str:
    level = generator.choices(
        ("INFO", "WARN", "ERROR", "MALFORMED"), weights=_LEVEL_WEIGHTS, k=1
    )[0]
    if level == "MALFORMED":
        return generator.choice(_MALFORMED_LINES)

    if level == "INFO":
        message = generator.choice(_INFO_MESSAGES)
    elif level == "WARN":
        message = generator.choice(_WARN_MESSAGES)
        if generator.random() < 0.1:
            level = "WARNING"
    else:
        message = generator.choice(_ERROR_MESSAGES)

    return f"{timestamp:%Y-%m-%d %H:%M:%S} {level} {message}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a synthetic log file.")
    parser.add_argument("--size-mb", type=float, required=True)
    parser.add_argument("--out", required=True)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    try:
        bytes_written = generate_log(arguments.size_mb, arguments.out)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(f"Generated {arguments.out} ({bytes_written} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
