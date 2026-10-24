# Implementation plan: logscope

This plan follows `SPEC.md` as the source of truth and implements one step at a time. At the end of every implementation step, run `python -m pytest -q`; do not start the following step unless it passes. Each completed step should be committed separately as `<step>: <short summary>`.

## 1. Project setup (`pyproject.toml`, `.gitignore`, folder structure)

- **Files to create**
  - `pyproject.toml`
  - `logscope/__init__.py`
  - `logscope/cli.py`
  - `logscope/parser.py`
  - `logscope/summary.py`
  - `logscope/timeline.py`
  - `logscope/grep.py`
  - `logscope/formatters.py`
  - `tests/__init__.py`
  - `tests/fixtures/.gitkeep`
  - `scripts/gen_log.py`
  - `scripts/bench.py`
- **Provided acceptance input**
  - Root-level `sample.log`; do not create a replacement sample log.
- **Files to update**
  - `.gitignore` to ignore generated `*.log` files while preserving the provided `sample.log` and `tests/fixtures/*.log`.
- **Main functions / configuration**
  - Configure the `logscope` console script entry point to call `logscope.cli:main`.
  - Establish the package and test directories from the required layout.
  - Add a minimal `main()` with argparse and empty subcommands so `logscope --help` works from step 1.
- **Tests**
  - Add a packaging/CLI smoke test that imports the package and invokes help through `main()` without reading a log file.
  - Verify the console-entry configuration through installed-package use during manual validation.
- **Streaming / memory approach**
  - No log processing occurs in setup. The initial module interfaces will accept iterators or file paths rather than preloaded line collections, preventing later APIs from encouraging whole-file reads.

## 2. Parser

- **Files to create**
  - `tests/test_parser.py`
  - `tests/fixtures/valid.log`
  - `tests/fixtures/malformed.log`
  - `tests/fixtures/empty.log`
- **Files to update**
  - `logscope/parser.py`
- **Main functions**
  - `LogEntry` dataclass containing the parsed timestamp, level, message, original line, and one-based line number as needed by downstream commands.
  - `parse_line(line: str) -> LogEntry | None`, which trims only the message field for validation and never raises for malformed input.
  - `iter_entries(file_path)` generator that opens using `errors="replace"`, enumerates the file object line by line, counts blank lines as total physical lines while excluding them from parsing and malformed counts, and yields parsed entries plus enough malformed-result information for callers to count failures without reparsing.
  - A compiled regex and `datetime.strptime()` validation for the accepted timestamp and levels.
- **Tests**
  - Valid INFO/WARN/ERROR parsing, `WARNING` normalization to `WARN`, message whitespace trimming, and preservation of the original line for text grep output.
  - Blank-line behavior, missing/invalid timestamps, unknown levels, empty messages, stack-trace continuation lines, and invalid UTF-8 replacement behavior.
  - Assert that parsing malformed content returns `None` rather than raising.
- **Streaming / memory approach**
  - Iterate directly over the file object; do not call `.read()`, `.readlines()`, `list()`, or sort/store log lines.
  - Yield one result at a time so each command retains only its specific aggregate or emits its output immediately.

## 3. `summary` command

- **Files to create**
  - `tests/test_summary.py`
  - `tests/fixtures/summary.log`
- **Files to update**
  - `logscope/summary.py`
  - `logscope/cli.py`
- **Main functions**
  - `summarize(file_path)` returning plain summary data: total physical lines, parsed lines, malformed lines, fixed INFO/WARN/ERROR counts, top five error messages, and minimum/maximum parsed timestamps.
  - A bounded top-error selection helper that orders by descending frequency then alphabetical message for ties.
  - CLI subcommand registration and error mapping: unreadable/missing file to exit code 1; invalid user arguments to exit code 2.
- **Tests**
  - Normal aggregation, all three level counts when zero, earliest/latest timestamps from out-of-order entries, top-five selection, alphabetical ties, and malformed count.
  - Empty and all-malformed fixtures, including `None` timestamps in command data.
  - Missing/unreadable-file exit behavior.
- **Streaming / memory approach**
  - Scan entries once. Retain scalar counters, min/max timestamps, and an error-message frequency map only; no entries or lines are collected.
  - Select the top five only after the scan from distinct error-message counts, never from a list of all errors.

## 4. `timeline` command

- **Files to create**
  - `tests/test_timeline.py`
  - `tests/fixtures/timeline.log`
- **Files to update**
  - `logscope/timeline.py`
  - `logscope/cli.py`
- **Main functions**
  - `parse_bucket(value: str) -> timedelta` accepting only positive `<N>m` or `<N>h` values and reporting invalid input as an argument error.
  - `floor_to_bucket(timestamp, bucket)` to align buckets to wall-clock boundaries.
  - `build_timeline(file_path, bucket)` returning malformed count and error counts keyed by bucket start.
  - Bucket-range iteration that fills zero-count buckets from the earliest error bucket through the latest error bucket.
- **Tests**
  - Default and custom minute/hour buckets, boundary alignment, errors spanning multiple buckets, zero-filled intermediate buckets, and no-error behavior.
  - Invalid bucket syntax and invalid/zero durations with exit code 2.
  - Empty and all-malformed inputs, malformed counts, and out-of-order log entries.
- **Streaming / memory approach**
  - Read once and retain only `ERROR` bucket counts plus earliest/latest error bucket and malformed counter.
  - Generate the final chronological bucket sequence from the bounded range; do not retain parsed entries or raw lines.

## 5. `grep` command

- **Files to create**
  - `tests/test_grep.py`
  - `tests/fixtures/grep.log`
- **Files to update**
  - `logscope/grep.py`
  - `logscope/cli.py`
- **Main functions**
  - `parse_since(value: str) -> datetime` accepting the two specified timestamp forms and treating the comparison as inclusive.
  - Level validation for `INFO`, `WARN`, and `ERROR`.
  - `entry_matches(entry, level, since)` that applies filters using AND semantics.
  - A streaming match iterator for text output and JSON output writing helpers coordinated with `formatters.py`.
- **Tests**
  - Unfiltered valid entries; individual level and since filters; combined AND filtering; inclusive minute/second boundaries; invalid level/since argument errors.
  - Exact original-line text output and malformed count on stderr.
  - Empty and all-malformed input, malformed counts in structured output, and out-of-order timestamps.
- **Streaming / memory approach**
  - Process each parsed result immediately. Text output writes matching original lines as encountered.
  - JSON writes its opening document, each match separated by commas, and closing document incrementally; it stores only the current match and counters, not a `matches` list.

## 6. Output formats (`json` and `md`)

- **Files to create**
  - `tests/test_formatters.py`
- **Files to update**
  - `logscope/formatters.py`
  - `logscope/cli.py`
  - `logscope/summary.py`
  - `logscope/timeline.py`
  - `logscope/grep.py`
- **Main functions**
  - Text, JSON, and Markdown renderers that accept already-computed plain command data.
  - JSON scalar/date conversion helpers that preserve one valid JSON document per command.
  - Markdown path creation using `logscope-<command>-<YYYYMMDD-HHMMSS>.md`, with `--output` override handling, overwrite behavior for existing paths, and stdout reporting only the written path.
  - `--output <path>` CLI validation that permits the option only with `--format md` and exits with code 2 for text or JSON.
  - Markdown layouts required by the specification: command/file heading and tables for summary data; timeline bars and grep matches as original lines in code blocks.
  - Timeline text bar scaling so the maximum nonzero bar is 50 characters.
- **Tests**
  - Text/JSON/Markdown output for each command, including fixed summary levels, `null`/`n/a` no-valid-line values, malformed count inclusion, and deterministic top-five and bucket output.
  - JSON validity using `json.loads()` and expected JSON schema/content.
  - Markdown default filename creation, explicit output path, overwrite behavior, stdout path reporting, and code-block rendering for timeline bars and grep original lines.
  - Reject `--output` with text or JSON using exit code 2.
  - Grep text malformed count on stderr and JSON incremental-document validity with zero/multiple matches.
- **Streaming / memory approach**
  - Summary and timeline render only their small aggregate data.
  - Grep uses format-specific streaming writers; Markdown and JSON generation must not first construct a list of matching entries or a full document string.

## 7. 100 MB log generator and benchmark script

- **Files to create**
  - `tests/test_scripts.py`
- **Files to update**
  - `scripts/gen_log.py`
  - `scripts/bench.py`
  - `.gitignore` if needed to verify generated logs remain ignored
- **Main functions**
  - `generate_log(size_mb, output_path)` that emits realistic valid and malformed lines until the requested approximate byte size is reached.
  - Generator CLI options `--size-mb` and `--out` as specified.
  - Benchmark runner that invokes all three commands (`summary`, `timeline`, and `grep`), measures elapsed runtime, and reports per-command peak RSS using `psutil`.
  - Declare `psutil` as a development-only dependency used exclusively by `scripts/bench.py` and its tests; the installed `logscope` tool remains standard-library-only.
  - Clear benchmark output showing input size, command, duration, exit status, and peak-memory metric.
- **Tests**
  - Small-size generator test using `tmp_path`, checking output size range and parseable representative content without generating 100 MB during tests.
  - Benchmark smoke test on a tiny generated fixture, verifying metrics for all three commands are reported and each command succeeds.
  - Manual acceptance run: generate 100 MB, benchmark processing, confirm under-60-second runtime and stable peak memory target; do not commit the generated log.
- **Streaming / memory approach**
  - The generator writes one line at a time and tracks byte count; it never builds the output log in memory.
  - The benchmark streams subprocess output or suppresses it safely and measures each child process without loading the input file; generated benchmark artifacts stay ignored.

## Deferred scope

- The stretch `explain` command is explicitly deferred and is not included in this implementation plan.
