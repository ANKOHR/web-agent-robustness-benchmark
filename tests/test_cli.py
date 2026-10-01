import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
from web_agent_robustness_benchmark.cli import main, read_records, InputError


def setup_fixture(tmp_path):
    directory = tmp_path / "input"
    main(["fixtures", "--out", str(directory)])
    return directory, tmp_path / "results.json"


def test_run_completes_on_fixture(tmp_path):
    directory, results = setup_fixture(tmp_path)
    start = time.perf_counter()
    assert main(["run", "--input", str(directory), "--results", str(results)]) == 0
    assert main(["report", "--results", str(results), "--format", "md"]) == 0
    assert time.perf_counter() - start < 5


def test_empty_input_renders_without_traceback(tmp_path, capsys):
    results = tmp_path.parent / (tmp_path.name + "-results.json")
    assert main(["run", "--input", str(tmp_path), "--results", str(results)]) == 0
    assert main(["report", "--results", str(results)]) == 0
    assert json.loads(results.read_text())["totals"]["records"] == 0
    assert "Traceback" not in capsys.readouterr().out


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.jsonl").write_text('# synthetic: true\n{bad}\n')
    assert main(["validate", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "bad.jsonl" in error and "line 2" in error


@pytest.mark.parametrize("suffix", ["csv", "yaml"])
def test_unsupported_format_named_error(tmp_path, capsys, suffix):
    (tmp_path / f"bad.{suffix}").write_text("{bad")
    assert main(["validate", "--input", str(tmp_path)]) == 2
    assert "unsupported input format" in capsys.readouterr().err


def test_schema_error_names_field_file_line(tmp_path, capsys):
    (tmp_path / "drift.jsonl").write_text('{}\n')
    assert main(["validate", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "drift.jsonl" in error and "line 1" in error and "baseline_success" in error


def test_missing_input_named_error(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err


def test_report_write_failure_no_partial_files(tmp_path, capsys):
    directory, results = setup_fixture(tmp_path)
    main(["run", "--input", str(directory), "--results", str(results)])
    destination = tmp_path / "directory"
    destination.mkdir()
    assert main(["report", "--results", str(results), "--out", str(destination)]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert not list(tmp_path.glob(".warb-write-*"))
    assert destination.is_dir()


def test_atomic_write_preserves_existing_on_failure(tmp_path, monkeypatch):
    from web_agent_robustness_benchmark.cli import atomic_write
    path = tmp_path / "report.md"
    path.write_text("original")
    def fail(*args):
        raise OSError("planted replace failure")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        atomic_write(path, "new")
    assert path.read_text() == "original"
    assert not list(tmp_path.glob(".warb-write-*"))


def test_cli_smoke_all_subcommands(tmp_path, capsys):
    directory, results = setup_fixture(tmp_path)
    for command in ("validate", "compare"):
        assert main([command, "--input", str(directory)]) == 0
    assert main(["run", "--input", str(directory), "--results", str(results)]) == 0
    for format in ("md", "json"):
        assert main(["report", "--results", str(results), "--format", format]) == 0
    assert "\u2014" not in capsys.readouterr().out
    for command in ("fixtures", "run", "report", "validate", "compare"):
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0
        assert "Example:" in capsys.readouterr().out


def test_result_files_byte_identical(tmp_path):
    directory, results = setup_fixture(tmp_path)
    args = ["run", "--input", str(directory), "--results", str(results)]
    main(args)
    first = results.read_bytes()
    main(args)
    assert results.read_bytes() == first


def test_json_array_input(tmp_path):
    from web_agent_robustness_benchmark.fixtures import fixture_records
    (tmp_path / "trials.json").write_text(json.dumps(fixture_records(2)))
    assert len(read_records(tmp_path)) == 2


def test_invalid_utf8_named_error(tmp_path, capsys):
    (tmp_path / "bad.jsonl").write_bytes(b"\xff")
    assert main(["validate", "--input", str(tmp_path)]) == 2
    assert "ParseError" in capsys.readouterr().err


def test_malformed_results_named_error(tmp_path, capsys):
    path = tmp_path / "results.json"
    path.write_text('{"schema_version": 1}')
    assert main(["report", "--results", str(path)]) == 2
    assert "ResultError" in capsys.readouterr().err


def test_subprocess_demo(tmp_path):
    root = Path(__file__).parents[1]
    env = dict(os.environ, PYTHONPATH=str(root), PYTHONIOENCODING="utf-8")
    commands = [["fixtures", "--out", "demo"], ["run", "--input", "demo"], ["report", "--format", "md"]]
    start = time.perf_counter()
    for args in commands:
        result = subprocess.run([sys.executable, "-m", "web_agent_robustness_benchmark.cli", *args],
            cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stderr
        assert "Traceback" not in result.stderr
    assert "Data provenance: 200 synthetic" in result.stdout
    assert time.perf_counter() - start < 5
