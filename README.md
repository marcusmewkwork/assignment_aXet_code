# logscope

`logscope` is a streaming CLI for incident-time application-log analysis. It gives the operations team summaries, error timelines, and filters directly in the terminal, without requiring a dashboard.

## Setup

Python 3.10+ is required.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Usage

```bash
logscope summary sample.log
logscope summary sample.log --format json
logscope summary sample.log --format md --output summary.md

logscope timeline sample.log --bucket 15m
logscope timeline sample.log --format json
logscope timeline sample.log --format md --output timeline.md

logscope grep sample.log --level ERROR --since "2026-10-01 09:30"
logscope grep sample.log --format json
logscope grep sample.log --format md --output grep.md
```

`md` writes a report file; `--output` is valid only with `--format md`.

## Tests

```bash
python -m pytest -q
```

## Generate and benchmark

```bash
python scripts/gen_log.py --size-mb 100 --out big100.log
python scripts/bench.py big100.log
```

See [PERF.md](PERF.md) for benchmark results. See [SPEC.md](SPEC.md) for behavior and [PLAN.md](PLAN.md) for the implementation plan.

## Known limitations

- Multi-line entries, including stack traces, are out of scope; continuation lines count as malformed.
- Compressed files, multiple input files, and live tailing are not supported.
