"""Core convergence metrics.

All metrics operate on a list of N strings (one per agent run). Tokenization
is whitespace-only and case-insensitive — this is a lexical comparison, not
semantic. For semantic convergence, pair these metrics with an embedding model
externally.
"""

from __future__ import annotations

from typing import Any


def tokenize(text: str) -> list[str]:
    """Whitespace tokenizer, lowercased. Intentionally simple."""
    return text.lower().split()


def exact_match_rate(runs: list[str]) -> float:
    """Fraction of runs identical to run[0]. Range [0, 1]. 1.0 if len(runs) < 2."""
    if len(runs) < 2:
        return 1.0
    first = runs[0]
    matches = sum(1 for r in runs if r == first)
    return round(matches / len(runs), 3)


def token_overlap(runs: list[str]) -> dict[str, float]:
    """Pairwise token set overlap across all run pairs.

    Returns:
        avg_overlap: mean pairwise Jaccard across all C(N,2) pairs. Range [0, 1].
        jaccard: Jaccard of the first two runs only (kept for quick eyeballing).

    If len(runs) < 2, returns {"avg_overlap": 1.0, "jaccard": 1.0} by convention.
    """
    if len(runs) < 2:
        return {"avg_overlap": 1.0, "jaccard": 1.0}

    tokenized = [set(tokenize(r)) for r in runs]
    union01 = tokenized[0] | tokenized[1]
    inter01 = tokenized[0] & tokenized[1]
    jaccard = len(inter01) / len(union01) if union01 else 0.0

    overlaps: list[float] = []
    for i in range(len(tokenized)):
        for j in range(i + 1, len(tokenized)):
            pair_union = tokenized[i] | tokenized[j]
            pair_inter = tokenized[i] & tokenized[j]
            if pair_union:
                overlaps.append(len(pair_inter) / len(pair_union))

    avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 1.0
    return {"avg_overlap": round(avg_overlap, 3), "jaccard": round(jaccard, 3)}


def divergence_point(runs: list[str]) -> dict[str, Any]:
    """Token position where outputs first differ.

    Returns:
        diverges_at_token: the token at the divergence position from run[0], or
            None if all runs are identical up to min length.
        token_position: 0-indexed position. Equals min_len if no divergence.
        num_tokens_to_divergence: alias for token_position, kept for readability.
    """
    if len(runs) < 2:
        return {"diverges_at_token": None, "token_position": 0, "num_tokens_to_divergence": 0}

    tokenized = [tokenize(r) for r in runs]
    min_len = min(len(t) for t in tokenized) if tokenized else 0

    for pos in range(min_len):
        tokens_at_pos = [t[pos] for t in tokenized]
        if len(set(tokens_at_pos)) > 1:
            return {
                "diverges_at_token": tokens_at_pos[0],
                "token_position": pos,
                "num_tokens_to_divergence": pos,
            }

    return {
        "diverges_at_token": None,
        "token_position": min_len,
        "num_tokens_to_divergence": min_len,
    }


def convergence_score(runs: list[str]) -> dict[str, float]:
    """Composite convergence score in [0, 1]. 1.0 = perfect convergence.

    Weighting (heuristic, not learned):
        0.5 * exact_match_rate
        0.3 * avg_token_overlap
        0.2 * normalized_divergence_distance   (where divergence at end = 1.0)

    Returns {"convergence_score": float}. If len(runs) < 2, returns 1.0.
    """
    if len(runs) < 2:
        return {"convergence_score": 1.0}

    exact = exact_match_rate(runs)
    overlap = token_overlap(runs)["avg_overlap"]
    div_pos = divergence_point(runs)["num_tokens_to_divergence"]
    max_tokens = max(len(tokenize(r)) for r in runs)
    div_distance = min(div_pos / max_tokens, 1.0) if max_tokens > 0 else 1.0

    score = 0.5 * exact + 0.3 * overlap + 0.2 * div_distance
    return {"convergence_score": round(score, 3)}


def score_runs(runs: list[str]) -> dict[str, Any]:
    """Compute all four metrics for a list of agent runs.

    Convenience wrapper. Returns a dict shaped for JSON output.
    """
    return {
        "num_runs": len(runs),
        "exact_match_rate": exact_match_rate(runs),
        "token_metrics": token_overlap(runs),
        "convergence_score": convergence_score(runs)["convergence_score"],
        "divergence_point": divergence_point(runs),
    }
