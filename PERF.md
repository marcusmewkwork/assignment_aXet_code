# Performance results

## Environment
- Python 3.11.2, running in WSL (Linux on Windows)
- Project on the Windows drive (`/mnt/c/...`), which is slower to read than native Linux storage
- Logs created with `scripts/gen_log.py` (fixed random seed, realistic mix of levels and messages, ~2% malformed)
- Measured with `scripts/bench.py` (wall-clock time and peak RSS via psutil)

## Results

| Log size | summary | timeline | grep | Peak memory |
|---|---|---|---|---|
| 5 MB | 1.1 s | 1.0 s | 1.9 s | ~14 MB |
| 10 MB | 2.4 s | 2.3 s | 4.7 s | ~14 MB |
| 50 MB | 8.8 s | 8.3 s | 16.4 s | ~14 MB |
| 100 MB | 18.1 s | 16.7 s | 34.4 s | ~14–15 MB |

## Conclusion
- **Speed:** all commands process a 100 MB log in under 60 s (slowest: grep, 34 s). Runtime grows linearly with file size.
- **Memory:** peak memory stays flat at ~14 MB while the file grows 20×, confirming the tool streams line by line instead of loading the whole file.

## How to reproduce
    python scripts/gen_log.py --size-mb 100 --out big100.log
    python scripts/bench.py big100.log
