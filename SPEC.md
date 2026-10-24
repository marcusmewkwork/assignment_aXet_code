# logscope: Specification

## 1. Purpose

After an incident, the operations team needs to summarise application logs from the terminal without opening a dashboard. `logscope` is a small CLI that reads a log file and produces summaries, error timelines and filtered views.

## 2. Log line format

Assumed format, one entry per line:

```
YYYY-MM-DD HH:MM:SS LEVEL message text
2026-10-01 09:15:23 ERROR Database connection timeout after 30s
```

- **Timestamp:** `YYYY-MM-DD HH:MM:SS`, local time, no timezone.
- **Level:** one of `INFO`, `WARN`, `ERROR`. Decision: `WARNING` is accepted and counted as `WARN`.
- **Message:** everything after the level, with surrounding whitespace trimmed. It must not be empty.

A line is **malformed** if any of the following is true:
- the timestamp is missing or doesn't parse
- the level isn't recognised
- the message is empty

   Blank lines count towards "total lines read" but are not parsed and not counted as malformed.

Multi-line entries such as stack traces are out of scope. Each continuation line counts as malformed.

## 3. Commands

### 3.1 `summary`

```
logscope summary <file> [--format text|json|md]
```

Reports:
- total lines read, lines parsed, malformed lines
- count per level (`INFO`, `WARN`, `ERROR`); all three are always shown, even when 0
- top 5 `ERROR` messages by frequency, with ties broken alphabetically
- first and last timestamp, meaning the **earliest and latest seen**, not the first and last line

If the file has no valid lines, all counts are 0 and the timestamps are `null` (JSON) or `n/a` (text).

### 3.2 `timeline`

```
logscope timeline <file> [--bucket 15m] [--format text|json|md]
```

- `--bucket` takes `<N>m` or `<N>h`, for example `5m`, `15m` or `1h`. The default is `15m`. Any other value exits with code 2 and a clear message.
- The command counts `ERROR` entries per bucket.
- Buckets are aligned to the clock (09:00, 09:15, 09:30 and so on), not to the first entry.
- Empty buckets between the first and last error are shown with a count of 0.
- In text mode, each bucket is one bar-chart row scaled so the longest bar is 50 characters:
  ```
  2026-10-01 09:00 | ████████████ 12
  2026-10-01 09:15 | ███ 3
  2026-10-01 09:30 |  0
  ```

### 3.3 `grep`

```
logscope grep <file> [--level LEVEL] [--since "YYYY-MM-DD HH:MM"] [--format text|json|md]
```

- Filters combine with AND. When no filter is given, every valid line is returned.
- `--since` is inclusive and accepts `YYYY-MM-DD HH:MM` or `YYYY-MM-DD HH:MM:SS`.
- Text mode prints the matching original lines unchanged, streamed as they are found.
- JSON mode returns `{"matches": [{"line_number", "timestamp", "level", "message"}...], "malformed_lines": N}`, written incrementally so memory stays flat.

## 4. Output formats (all commands)

| Format | Destination | Notes |
|---|---|---|
| `text` (default) | stdout | Human-readable |
| `json` | stdout | One valid JSON document |
| `md` | file | Writes `logscope-<command>-<YYYYMMDD-HHMMSS>.md` in the current folder (or the path given with `--output`) and prints that path |

Every format reports the malformed-line count. In `grep` text mode, the count goes to **stderr** so stdout stays clean for piping.

Markdown reports: a `#` heading with the command and file name, then tables for summary data; timeline bars and grep lines go inside a code block. An existing file is overwritten. `--output <path>` is only allowed with `--format md`; otherwise exit with code 2.

## 5. Non-functional requirements

- **Streaming:** the tool reads the file line by line. Memory use must not grow with file size. Only aggregates are held in memory: counters, buckets, and min/max timestamps.
- **Performance:** a 100 MB log is processed in under 60 s on a dev laptop, with stable peak memory (target under 100 MB RSS).
- **Robustness:** malformed lines and invalid UTF-8 bytes never crash the tool. Files are opened with `errors="replace"`.
- **Exit codes:** `0` means success, `1` means the file is missing or unreadable, `2` means invalid arguments.
- **Runtime:** Python 3.10+, standard library only for the tool itself. `pytest` is used for tests.

## 6. Out of scope

- Multi-line log entries
- Compressed files, multiple input files, live tailing

## 7. Stretch goal: `explain`

```
logscope explain <file>
```

Sends the top errors and the timeline to an LLM and prints a probable root-cause summary. The endpoint and key come from environment variables `LOGSCOPE_LLM_URL` and `LOGSCOPE_LLM_KEY`. If either is missing, the tool exits with a clear message. Tests mock the HTTP call.

## 8. Acceptance criteria

- [ ] All three commands work on the provided `sample.log`
- [ ] Unit tests for the parser and each command, all passing
- [ ] A 100 MB log is processed in under 60 s with stable memory
- [ ] The malformed-line count is reported
- [ ] Git history shows plan-then-build, not one large commit
