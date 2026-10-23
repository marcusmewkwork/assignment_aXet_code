# Project instructions (for aXet Code)

## Context
This repo builds `logscope`, a log-analysis CLI. **SPEC.md is the source of truth.** If the spec is ambiguous or silent on something, ask me rather than guessing. Never edit SPEC.md without my approval.

## Tech stack
- Python 3.10+ using only the standard library: `argparse`, `re`, `datetime`, `collections`, `json`, `pathlib`
- `pytest` for tests
- No pandas, no third-party CLI frameworks
- Installed as a package with a `logscope` console entry point in `pyproject.toml`

## Layout
```
logscope/
  __init__.py
  cli.py          # argparse, subcommands, exit codes
  parser.py       # parse_line() and iter_entries()
  summary.py
  timeline.py
  grep.py
  formatters.py   # text / json / md rendering
tests/
  fixtures/       # small hand-written logs, including malformed lines
scripts/
  gen_log.py      # synthetic log generator
  bench.py        # runtime + peak-memory measurement
```

## Hard rules
1. **Stream everything.** Iterate the file object line by line. Never use `.read()`, `.readlines()`, `list(f)`, or anything else that sorts or stores all lines.
2. **The parser never raises.** `parse_line(line) -> LogEntry | None` returns `None` for malformed input. The caller counts the `None` results.
3. **Separate computing from rendering.** Commands return plain data, such as a dataclass or dict. `formatters.py` turns that data into text, JSON or Markdown. This keeps the commands testable.
4. **Work one PLAN.md step at a time.** At the end of each step:
   - run `python -m pytest -q` and show me the output
   - don't start the next step if any test fails
   - commit with the message `<step>: <short summary>`, one commit per step
5. **Never commit generated large logs.** `*.log` is git-ignored, except `sample.log` and `tests/fixtures/*.log`.

## Commands
- Install: `pip install -e .`
- Test: `python -m pytest -q`
- Run: `logscope summary sample.log`
- Generate test log: `python scripts/gen_log.py --size-mb 100 --out big.log`
- Benchmark: `python scripts/bench.py big.log`

## Testing expectations
- Each command gets tests for normal input, an empty file, an all-malformed file, and its edge cases (bucket boundaries, inclusive `--since`, top-5 ties).
- Tests use small fixture files or `tmp_path`, never the 100 MB log.
