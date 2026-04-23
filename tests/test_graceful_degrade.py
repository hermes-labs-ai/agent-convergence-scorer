"""Graceful-degradation tests — required by the hermes-seal continuity gate.

The tool is stdlib-only and has no external dependencies (no network, no disk
beyond the user-provided input file). There is therefore nothing that can fail
on the user's behalf — but boundary inputs must still produce a clean error
message on stderr and a non-zero exit code, never a stacktrace or silent empty
output. Each test asserts exactly that contract.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agent_convergence_scorer", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_clean_error(proc: subprocess.CompletedProcess[str], token: str) -> None:
    assert proc.returncode != 0, f"expected non-zero exit, got {proc.returncode}"
    assert proc.stdout == "", f"expected empty stdout on error, got: {proc.stdout!r}"
    assert token in proc.stderr, f"expected error token {token!r} in stderr, got: {proc.stderr!r}"
    assert "Traceback" not in proc.stderr, f"stacktrace leaked to stderr:\n{proc.stderr}"


def test_degrade_missing_file(tmp_path: Path):
    proc = _run([str(tmp_path / "does_not_exist.json")])
    _assert_clean_error(proc, "file not found")


def test_degrade_malformed_json(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid json")
    proc = _run([str(p)])
    _assert_clean_error(proc, "invalid JSON")


def test_degrade_empty_list(tmp_path: Path):
    p = tmp_path / "empty.json"
    p.write_text(json.dumps([]))
    proc = _run([str(p)])
    _assert_clean_error(proc, "non-empty list")


def test_degrade_wrong_element_type(tmp_path: Path):
    p = tmp_path / "numbers.json"
    p.write_text(json.dumps([1, 2, 3]))
    proc = _run([str(p)])
    _assert_clean_error(proc, "must be strings")


def test_degrade_no_arguments():
    proc = _run([])
    # argparse emits its own error and exits 2
    assert proc.returncode == 2
    assert "the following arguments are required" in proc.stderr
    assert "Traceback" not in proc.stderr
