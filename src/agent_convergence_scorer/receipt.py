"""Hermes-shaped post-run evidence receipts.

This adapter deliberately preserves the public score schema in ``scorer``.
It converts structured parallel-agent outputs into a separately versioned,
non-approval receipt.  The signal remains lexical only.
"""

from __future__ import annotations

import math
from typing import Any

RECEIPT_SCHEMA = "agent-convergence-scorer.post-run-receipt.v1"


def extract_agent_results(payload: Any) -> tuple[list[str], list[str]]:
    """Return output text and agent IDs from Hermes-shaped result JSON.

    Required shape::

        {"results": [{"agent_id": "...", "output": "..."}, ...]}

    Extra top-level and per-result metadata is preserved by the caller, not
    interpreted here.  This keeps the adapter independent of orchestration
    providers while giving it a stable, inspectable boundary.
    """
    if not isinstance(payload, dict):
        raise ValueError("receipt input must be an object with a 'results' list")
    results = payload.get("results")
    if not isinstance(results, list) or len(results) < 2:
        raise ValueError("receipt input 'results' must contain at least two results")

    agent_ids: list[str] = []
    outputs: list[str] = []
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            raise ValueError(f"receipt result {index} must be an object")
        agent_id = result.get("agent_id")
        output = result.get("output")
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError(f"receipt result {index} requires a non-empty string 'agent_id'")
        if not isinstance(output, str):
            raise ValueError(f"receipt result {index} requires a string 'output'")
        agent_ids.append(agent_id)
        outputs.append(output)
    if len(set(agent_ids)) != len(agent_ids):
        raise ValueError("receipt result 'agent_id' values must be unique")
    return agent_ids, outputs


def make_post_run_receipt(payload: Any, minimum_convergence: float) -> dict[str, Any]:
    """Create a review/investigate-only receipt for parallel agent results."""
    from agent_convergence_scorer.scorer import score_runs

    if not isinstance(minimum_convergence, (int, float)) or isinstance(minimum_convergence, bool):
        raise ValueError("minimum_convergence must be a finite number in [0, 1]")
    if not math.isfinite(minimum_convergence) or not 0.0 <= minimum_convergence <= 1.0:
        raise ValueError("minimum_convergence must be a finite number in [0, 1]")
    agent_ids, outputs = extract_agent_results(payload)
    score = score_runs(outputs)
    passed = score["convergence_score"] >= minimum_convergence
    source = {
        key: payload[key]
        for key in ("schema", "task_id")
        if isinstance(payload.get(key), str)
    }
    return {
        "schema": RECEIPT_SCHEMA,
        "source": source,
        "signal_kind": "lexical_output_convergence",
        "agent_ids": agent_ids,
        "score": score,
        "minimum_convergence": {"threshold": minimum_convergence, "passed": passed},
        "decision": "review" if passed else "investigate",
        "acceptance_authority": False,
        "limitations": [
            "Lexical output convergence is not semantic agreement or correctness.",
            "This receipt cannot approve, accept, merge, deploy, or replace review/tests.",
        ],
    }
