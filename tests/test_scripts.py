import importlib.util
from pathlib import Path
import sys


def load_script_module(name: str):
    script_path = Path("scripts") / f"{name}.py"
    specification = importlib.util.spec_from_file_location(name, script_path)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def test_generate_log_writes_requested_approximate_size(tmp_path):
    gen_log = load_script_module("gen_log")
    output_path = tmp_path / "generated.log"

    bytes_written = gen_log.generate_log(0.01, output_path)

    assert output_path.stat().st_size == bytes_written
    assert bytes_written >= int(0.01 * 1024 * 1024)
    content = output_path.read_text(encoding="utf-8")
    assert "2026-10-01" in content
    assert " INFO " in content
    assert " WARN " in content or " WARNING " in content
    assert " ERROR " in content


def test_generate_log_is_deterministic(tmp_path):
    gen_log = load_script_module("gen_log")
    first_output = tmp_path / "first.log"
    second_output = tmp_path / "second.log"

    gen_log.generate_log(0.01, first_output)
    gen_log.generate_log(0.01, second_output)

    assert first_output.read_bytes() == second_output.read_bytes()


def test_benchmark_runs_all_commands_on_small_log(tmp_path):
    gen_log = load_script_module("gen_log")
    bench = load_script_module("bench")
    output_path = tmp_path / "generated.log"
    gen_log.generate_log(0.01, output_path)

    input_size, results = bench.benchmark(output_path)

    assert input_size == output_path.stat().st_size
    assert [result.command for result in results] == ["summary", "timeline", "grep"]
    assert all(result.exit_code == 0 for result in results)
    assert all(result.duration_seconds >= 0 for result in results)
    assert "peak RSS:" in bench.format_results(input_size, results)
