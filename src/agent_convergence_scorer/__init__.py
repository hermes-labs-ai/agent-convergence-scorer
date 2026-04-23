"""agent-convergence-scorer — measure how similar N agent outputs are."""

from agent_convergence_scorer.scorer import (
    convergence_score,
    divergence_point,
    exact_match_rate,
    score_runs,
    token_overlap,
    tokenize,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "convergence_score",
    "divergence_point",
    "exact_match_rate",
    "score_runs",
    "token_overlap",
    "tokenize",
]
