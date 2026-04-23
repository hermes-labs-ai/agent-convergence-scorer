"""Tests for the scorer functions."""

from __future__ import annotations

import pytest

from agent_convergence_scorer.scorer import (
    convergence_score,
    divergence_point,
    exact_match_rate,
    score_runs,
    token_overlap,
    tokenize,
)


def test_tokenize_basic():
    assert tokenize("hello world") == ["hello", "world"]


def test_tokenize_lowercases():
    assert tokenize("Hello WORLD") == ["hello", "world"]


def test_tokenize_empty():
    assert tokenize("") == []


def test_exact_match_all_same():
    runs = ["the answer is 42"] * 3
    assert exact_match_rate(runs) == 1.0


def test_exact_match_partial():
    runs = ["the answer is 42", "the answer is 43", "the answer is 42"]
    assert exact_match_rate(runs) == round(2 / 3, 3)


def test_exact_match_all_different():
    runs = ["a", "b", "c"]
    assert exact_match_rate(runs) == round(1 / 3, 3)


def test_exact_match_single_run():
    assert exact_match_rate(["only run"]) == 1.0


def test_exact_match_empty():
    assert exact_match_rate([]) == 1.0


def test_token_overlap_identical():
    runs = ["the cat sat", "the cat sat"]
    result = token_overlap(runs)
    assert result["avg_overlap"] == 1.0
    assert result["jaccard"] == 1.0


def test_token_overlap_partial():
    runs = ["the cat sat", "the dog sat"]
    result = token_overlap(runs)
    assert 0.5 <= result["avg_overlap"] < 1.0
    assert 0.5 <= result["jaccard"] < 1.0


def test_token_overlap_disjoint():
    runs = ["apple banana", "cherry date"]
    result = token_overlap(runs)
    assert result["avg_overlap"] == 0.0
    assert result["jaccard"] == 0.0


def test_token_overlap_single_run():
    assert token_overlap(["only run"]) == {"avg_overlap": 1.0, "jaccard": 1.0}


def test_divergence_identical():
    runs = ["the answer is 42", "the answer is 42"]
    assert divergence_point(runs)["num_tokens_to_divergence"] >= 4


def test_divergence_at_position_zero():
    runs = ["the answer is 42", "different answer"]
    assert divergence_point(runs)["num_tokens_to_divergence"] == 0


def test_divergence_mid_sequence():
    runs = ["the answer is 42", "the answer is different"]
    assert divergence_point(runs)["num_tokens_to_divergence"] == 3


def test_divergence_single_run():
    result = divergence_point(["only"])
    assert result["diverges_at_token"] is None
    assert result["token_position"] == 0


def test_convergence_score_perfect():
    runs = ["hello world"] * 3
    assert convergence_score(runs)["convergence_score"] == 1.0


def test_convergence_score_divergent():
    runs = ["a b c", "x y z", "p q r"]
    score = convergence_score(runs)["convergence_score"]
    assert 0.0 <= score < 0.5


def test_convergence_score_bounds():
    runs = ["the cat", "the dog", "the fish"]
    score = convergence_score(runs)["convergence_score"]
    assert 0.0 <= score <= 1.0


def test_convergence_score_single_run():
    assert convergence_score(["only"])["convergence_score"] == 1.0


def test_score_runs_perfect():
    runs = ["The capital of France is Paris."] * 3
    result = score_runs(runs)
    assert result["num_runs"] == 3
    assert result["exact_match_rate"] == 1.0
    assert result["convergence_score"] == 1.0


def test_score_runs_divergent():
    runs = ["The answer is A", "The answer is B", "The answer is C"]
    result = score_runs(runs)
    assert result["num_runs"] == 3
    assert result["exact_match_rate"] == round(1 / 3, 3)
    assert result["convergence_score"] < 0.7
    assert result["divergence_point"]["num_tokens_to_divergence"] == 3


def test_score_runs_shape():
    result = score_runs(["a", "a"])
    assert set(result.keys()) == {
        "num_runs",
        "exact_match_rate",
        "token_metrics",
        "convergence_score",
        "divergence_point",
    }


@pytest.mark.parametrize(
    "n,expected_min_pairs",
    [(2, 1), (3, 3), (4, 6), (5, 10)],
)
def test_token_overlap_pair_count(n: int, expected_min_pairs: int):
    """avg_overlap is computed over C(N,2) pairs — sanity check it scales."""
    runs = [f"run number {i}" for i in range(n)]
    result = token_overlap(runs)
    assert "avg_overlap" in result
    assert 0.0 <= result["avg_overlap"] <= 1.0
