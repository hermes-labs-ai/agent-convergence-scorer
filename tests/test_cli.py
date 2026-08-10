"""Tests for the CLI entry point."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agent_convergence_scorer.cli import THRESHOLD_NOT_MET_EXIT_CODE, _extract_runs, main


def _write_json(tmp_path: Path, obj: object) -> Path:
    p = tmp_path / "input.json"
    p.write_text(json.dumps(obj))
    return p


def _module_env() -> dict[str, str]:
    source_root = Path(__file__).resolve().parents[1] / "src"
    existing = os.environ.get("PYTHONPATH", "")
    return {**os.environ, "PYTHONPATH": f"{source_root}{os.pathsep}{existing}"}


def test_extract_runs_list():
    assert _extract_runs(["a", "b"]) == ["a", "b"]


def test_extract_runs_dict():
    assert _extract_runs({"runs": ["a", "b"]}) == ["a", "b"]


def test_extract_runs_empty_raises():
    with pytest.raises(ValueError):
        _extract_runs([])


def test_extract_runs_non_string_raises():
    with pytest.raises(ValueError):
        _extract_runs([1, 2, 3])


def test_main_happy_path(tmp_path, capsys):
    p = _write_json(tmp_path, {"runs": ["hello world"] * 3})
    rc = main([str(p)])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["num_runs"] == 3
    assert parsed["exact_match_rate"] == 1.0


def test_main_list_shape(tmp_path, capsys):
    p = _write_json(tmp_path, ["a", "b", "c"])
    rc = main([str(p)])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["num_runs"] == 3


def test_main_missing_file(tmp_path, capsys):
    rc = main([str(tmp_path / "nope.json")])
    assert rc == 1
    assert "file not found" in capsys.readouterr().err


def test_main_invalid_json(tmp_path, capsys):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    rc = main([str(p)])
    assert rc == 1
    assert "invalid JSON" in capsys.readouterr().err


def test_main_empty_list(tmp_path, capsys):
    p = _write_json(tmp_path, [])
    rc = main([str(p)])
    assert rc == 1
    assert "non-empty list" in capsys.readouterr().err


def test_main_wrong_types(tmp_path, capsys):
    p = _write_json(tmp_path, [1, 2, 3])
    rc = main([str(p)])
    assert rc == 1
    assert "must be strings" in capsys.readouterr().err


def test_main_stdin(monkeypatch, capsys):
    payload = json.dumps({"runs": ["a", "a"]})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    rc = main(["-"])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["exact_match_rate"] == 1.0


def test_main_indent_zero_compact(tmp_path, capsys):
    p = _write_json(tmp_path, ["x", "y"])
    rc = main(["--indent", "0", str(p)])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert "\n" not in out


def test_minimum_convergence_equality_passes_with_machine_readable_result(tmp_path, capsys):
    p = _write_json(tmp_path, ["same", "different"])
    rc = main(["--min-convergence", "0.25", str(p)])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["convergence_score"] == 0.25
    assert parsed["minimum_convergence"] == {"threshold": 0.25, "passed": True}


def test_minimum_convergence_failure_keeps_json_and_reports_human_error(tmp_path, capsys):
    p = _write_json(tmp_path, ["same", "different"])
    rc = main(["--min-convergence", "0.251", str(p)])
    assert rc == THRESHOLD_NOT_MET_EXIT_CODE
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["minimum_convergence"] == {"threshold": 0.251, "passed": False}
    assert "convergence score 0.25 is below minimum 0.251" in captured.err


def test_minimum_convergence_stdin_failure_is_machine_readable(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(["same", "different"])))
    rc = main(["--min-convergence", "0.251", "-"])
    assert rc == THRESHOLD_NOT_MET_EXIT_CODE
    captured = capsys.readouterr()
    assert json.loads(captured.out)["minimum_convergence"]["passed"] is False
    assert "below minimum" in captured.err


@pytest.mark.parametrize("value", ["-0.1", "1.1", "nan", "NaN", "inf", "-inf", "not-a-number"])
def test_minimum_convergence_invalid_values_are_usage_errors(tmp_path, value: str):
    p = _write_json(tmp_path, ["a", "a"])
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_convergence_scorer",
            "--min-convergence",
            value,
            str(p),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_module_env(),
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "--min-convergence" in result.stderr
    assert "finite number in [0, 1]" in result.stderr


def test_cli_help_discloses_minimum_convergence_contract():
    result = subprocess.run(
        [sys.executable, "-m", "agent_convergence_scorer", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env=_module_env(),
    )
    assert result.returncode == 0
    help_text = " ".join(result.stdout.split())
    assert "inclusive minimum reported convergence score" in help_text
    assert "finite in [0, 1]" in help_text
    assert "failure exits 3" in help_text
    assert "JSON stdout valid" in help_text
    assert "human-readable failure to stderr" in help_text


def test_cli_module_invocation(tmp_path):
    p = _write_json(tmp_path, ["a", "a"])
    result = subprocess.run(
        [sys.executable, "-m", "agent_convergence_scorer", str(p)],
        capture_output=True,
        text=True,
        check=False,
        env=_module_env(),
    )
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed["exact_match_rate"] == 1.0
