"""Tests for the post-run receipt adapter's explicit non-approval boundary."""

from __future__ import annotations

import json
import math

import pytest

from agent_convergence_scorer.cli import THRESHOLD_NOT_MET_EXIT_CODE, main
from agent_convergence_scorer.receipt import RECEIPT_SCHEMA, make_post_run_receipt


def _payload(outputs: list[str]) -> dict[str, object]:
    return {
        "schema": "hermes.parallel-agent-results.v1",
        "results": [
            {"agent_id": f"agent-{index}", "output": output}
            for index, output in enumerate(outputs)
        ],
    }


def test_receipt_maps_hermes_results_to_review_only_signal():
    receipt = make_post_run_receipt(_payload(["same result", "same result", "same result"]), 0.7)

    assert receipt["schema"] == RECEIPT_SCHEMA
    assert receipt["source"] == {"schema": "hermes.parallel-agent-results.v1"}
    assert receipt["agent_ids"] == ["agent-0", "agent-1", "agent-2"]
    assert receipt["decision"] == "review"
    assert receipt["acceptance_authority"] is False
    assert receipt["score"]["num_runs"] == 3


def test_receipt_threshold_failure_keeps_json_and_exits_for_investigation(tmp_path, capsys):
    path = tmp_path / "results.json"
    path.write_text(json.dumps(_payload(["alpha", "beta", "gamma"])))

    rc = main(["receipt", "--min-convergence", "0.9", str(path)])

    captured = capsys.readouterr()
    receipt = json.loads(captured.out)
    assert rc == THRESHOLD_NOT_MET_EXIT_CODE
    assert receipt["decision"] == "investigate"
    assert receipt["minimum_convergence"]["passed"] is False
    assert "investigate required" in captured.err


def test_receipt_never_has_acceptance_decision():
    receipt = make_post_run_receipt(_payload(["same", "same"]), 0.0)

    assert receipt["decision"] in {"review", "investigate"}
    assert receipt["acceptance_authority"] is False
    assert "accept" not in receipt["decision"]


@pytest.mark.parametrize(
    "payload, error",
    [
        (_payload(["only one"]), "at least two results"),
        (
            {
                "results": [
                    {"agent_id": "same", "output": "first"},
                    {"agent_id": "same", "output": "second"},
                ]
            },
            "must be unique",
        ),
    ],
)
def test_receipt_rejects_trivial_or_duplicated_evidence(payload, error):
    with pytest.raises(ValueError, match=error):
        make_post_run_receipt(payload, 0.7)


@pytest.mark.parametrize("threshold", [-0.1, 1.1, math.nan, math.inf, "0.7", True])
def test_receipt_library_rejects_invalid_thresholds(threshold):
    with pytest.raises(ValueError, match="finite number"):
        make_post_run_receipt(_payload(["same", "same"]), threshold)


def test_receipt_carries_optional_source_identifiers_without_outputs():
    payload = _payload(["same", "same"])
    payload["schema"] = "hermes.parallel-agent-results.v1"
    payload["task_id"] = "parallel-eval-42"

    receipt = make_post_run_receipt(payload, 0.7)

    assert receipt["source"] == {
        "schema": "hermes.parallel-agent-results.v1",
        "task_id": "parallel-eval-42",
    }
    assert "results" not in receipt["source"]
