# agent-convergence-scorer

agent-convergence-scorer is a CLI and Python library that scores how lexically similar N agent outputs are — exact-match rate, Jaccard token overlap, divergence point, and a composite 0–1 convergence score over any list of agent runs. Comparison is whitespace-lexical, not semantic (see [When not to use it](#when-not-to-use-it)).

[![PyPI](https://img.shields.io/pypi/v/agent-convergence-scorer.svg)](https://pypi.org/project/agent-convergence-scorer/)
[![Python](https://img.shields.io/pypi/pyversions/agent-convergence-scorer.svg)](https://pypi.org/project/agent-convergence-scorer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/hermes-labs-ai/agent-convergence-scorer/actions/workflows/ci.yml/badge.svg)](https://github.com/hermes-labs-ai/agent-convergence-scorer/actions/workflows/ci.yml)

If you run the same prompt through N agents and want a number for "are they producing N distinct outputs or have they collapsed to one idea?" — this is that number.

## Pain

- You just ran a fan-out of N agents and eyeballing whether they converged is slow and subjective.
- Your eval harness reports accuracy but not *reproducibility*; same prompt, two runs, two answers, no metric.
- Multi-agent hackathon or swarm setup; half the agents picked the same target. You want evidence, not vibes.
- LLM temperature study where "temp=0.3 vs temp=0.7" needs a downstream consistency number.
- You caught agents rephrasing each other but there is no column in your CSV for it.

## Install

```bash
pip install agent-convergence-scorer
```

Python 3.9+. Zero runtime dependencies (stdlib only).

## Quick start

```bash
echo '{"runs": ["The capital is Paris.", "The capital is Paris.", "The capital is Lyon."]}' \
  | agent-convergence-scorer -
```

Output:

```json
{
  "num_runs": 3,
  "exact_match_rate": 0.667,
  "token_metrics": {
    "avg_overlap": 0.733,
    "jaccard": 1.0
  },
  "convergence_score": 0.703,
  "divergence_point": {
    "diverges_at_token": "paris.",
    "token_position": 3,
    "num_tokens_to_divergence": 3
  }
}
```

### Optional CI threshold

Use `--min-convergence` to fail a job when the same public score reported in
the JSON is below an inclusive threshold. This command passes because the
score is exactly `1.0`:

```bash
printf '%s\n' '{"runs": ["same output", "same output"]}' \
  | agent-convergence-scorer --min-convergence 1.0 -
```

When the option is supplied, the otherwise compatible JSON result gains this
one field:

```json
"minimum_convergence": {"threshold": 0.8, "passed": false}
```

The command exits `0` when the score is at least the threshold (including
equality), and `3` when it is below it. On a threshold failure it still writes
valid JSON to stdout and writes a concise explanation to stderr, so CI can
read `minimum_convergence.passed` without parsing human text. Without
`--min-convergence`, output and exit behavior are unchanged. Invalid threshold
values (including `NaN`, infinity, and values outside `[0, 1]`) are argparse
usage errors with exit code `2`.

Interpret:

- `convergence_score = 0.703` — high but not perfect consistency.
- `exact_match_rate = 0.667` — 2 of 3 runs identical to run 0.
- Divergence at token 3 — they agreed on the prefix "The capital is" then split.

## Library usage

```python
from agent_convergence_scorer import score_runs

runs = [
    "The answer is A",
    "The answer is B",
    "The answer is C",
]
print(score_runs(runs))
# {'num_runs': 3, 'exact_match_rate': 0.333,
#  'token_metrics': {'avg_overlap': 0.6, 'jaccard': 0.6},
#  'convergence_score': 0.497,
#  'divergence_point': {'diverges_at_token': 'a', 'token_position': 3, 'num_tokens_to_divergence': 3}}
```

Individual metrics are importable too: `exact_match_rate`, `token_overlap`, `divergence_point`, `convergence_score`, `tokenize`.

## Metrics — what they mean

| Metric | Range | What it measures |
|---|---|---|
| `exact_match_rate` | `[0, 1]` | Fraction of runs byte-identical to `runs[0]`. Crude reproducibility floor. |
| `token_metrics.jaccard` | `[0, 1]` | Token-set Jaccard of the first two runs (quick eyeball). |
| `token_metrics.avg_overlap` | `[0, 1]` | Mean Jaccard over all `C(N,2)` pairs. Robust to N. |
| `divergence_point.num_tokens_to_divergence` | `[0, min_len]` | First position where runs disagree. Late divergence = strong shared prefix. |
| `convergence_score` | `[0, 1]` | Composite: `0.5 * exact_match + 0.3 * avg_overlap + 0.2 * div_distance_norm`. |

## When to use it

- Quick single-number consistency check for multi-agent fan-outs.
- CI gate: fail if N reruns of a prompt drop below a convergence threshold.
- Measuring the effect of a temperature, prompt, or framing change on output stability.
- Quantifying ideation collapse in multi-agent hackathons (N agents → how many distinct ideas?).

## When not to use it

- **Semantic similarity.** Tokenization is whitespace-only; "Paris, France" and "paris, france," are different token sets. If you need meaning-level comparison, pair these metrics with a sentence-embedding similarity (or a reranker) externally.
- **Subword tokenization studies.** This is not a BPE/WordPiece tokenizer.
- **Multilingual corpora where whitespace isn't the word boundary** (Chinese, Japanese, Thai, etc.) — tokenize upstream, pass the tokenized-then-joined form.
- **Ranking quality** (nDCG, MRR, etc.) — use `ir-measures` or `ranx` instead.
- **Concurrency-safe incremental scoring over streams** — this is a batch tool.

The composite weights (50/30/20) are heuristic; override by calling the individual functions and combining yourself.

All exported scoring metrics reject `[]` with `ValueError`: no runs are not
evidence of convergence. A single run remains the defined trivial case.
For Jaccard overlap, two runs whose whitespace token sets are both empty have
overlap `1.0`; this applies even if their original bytes differ (for example,
`" "` and `"\t"`). Exact-match rate remains byte-exact. A
`divergence_point.diverges_at_token` of `null` means no token disagreement was
found before the shortest run ended; it does not prove the full runs are byte
identical, so prefix cases retain `null` in either direction.

## Example: measuring a hackathon collapse

```python
from agent_convergence_scorer import score_runs

# 4 agents, same prompt, different (or identical) outputs
runs = [agent.run(prompt) for agent in agents]
result = score_runs(runs)

if result["convergence_score"] > 0.8:
    print(f"⚠️ collapse: {result['convergence_score']:.2f} — agents are rephrasing each other")
else:
    print(f"✓ diverse: {result['convergence_score']:.2f}")
```

## Origin

Built during a [Hermes Labs](https://hermes-labs.ai) internal experiment on 2026-04-22 that looked at whether prompt framing affects how much N concurrent agents converge on the same output. This scorer is the measurement tool that came out of that work; the experimental results themselves are not part of this repository.

## Security and supply chain

- SBOM: `sbom.cdx.json` (CycloneDX 1.5) at repo root.
- Security policy: see [SECURITY.md](SECURITY.md).

## Part of the Hermes Labs reliability stack

Part of the [Hermes Labs reliability stack](https://github.com/hermes-labs-ai) of open-source tools for catching silent failure modes in production AI.

A complementary (not overlapping) sibling is [lintlang](https://github.com/hermes-labs-ai/lintlang): lintlang statically lints agent-config structure *before* a run; agent-convergence-scorer measures how much the actual outputs converge *after* N runs. Different layers — config-time vs runtime — not duplicates.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome. For agent-driven contributors, see [AGENTS.md](AGENTS.md).

## License

MIT — see [LICENSE](LICENSE).

---

## About Hermes Labs

[Hermes Labs](https://hermes-labs.ai) is an AI reliability engineering studio for product and engineering teams shipping production agents and LLM applications. We find the structural AI failures standard evals miss, then harden retrieval, memory, agents, and the language layers around production AI systems with runtime controls and defensible evidence.

Browse the [open-source catalog](https://hermes-labs.ai/open-source) or contact [roli@hermes-labs.ai](mailto:roli@hermes-labs.ai).

---

If this saved you the five minutes of eyeballing a fan-out's outputs, ⭐ the repo — it helps others find it.
