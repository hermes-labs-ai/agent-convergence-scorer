# agent-convergence-scorer

**Measure how similar N agent outputs are.** Score exact-match rate, Jaccard token overlap, divergence point, and a composite 0–1 convergence score over any list of agent runs.

[![PyPI](https://img.shields.io/pypi/v/agent-convergence-scorer.svg)](https://pypi.org/project/agent-convergence-scorer/)
[![Python](https://img.shields.io/pypi/pyversions/agent-convergence-scorer.svg)](https://pypi.org/project/agent-convergence-scorer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/roli-lpci/agent-convergence-scorer/actions/workflows/ci.yml/badge.svg)](https://github.com/roli-lpci/agent-convergence-scorer/actions/workflows/ci.yml)
[![Hermes Seal](https://img.shields.io/badge/hermes--seal-manifest%20staged-blue)](https://github.com/roli-lpci/hermes-seal)

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

Built during the [Hermes Labs](https://hermes-labs.ai) Cascade Hackathon on 2026-04-22, as part of a controlled experiment measuring whether prompt framing affects ideation diversity across N concurrent agents. In the prior-day baseline, 12 agents sharing context collapsed to 2 dominant idea clusters; in the cascade experiment, agents under distinct-persona or distinct-constraint framing produced 4 distinct clusters per arm of 4. This scorer is the mechanism by which the collapse was measured.

## Security and supply chain

- Tamper evidence: the repository carries a staged [hermes-seal](https://github.com/roli-lpci/hermes-seal) v1 manifest at `.hermes-seal.yaml`. Signature is granted out-of-band with a root-owned key and verified with `hermes-seal verify <path-to-repo>`.
- SBOM: `sbom.cdx.json` (CycloneDX 1.5) at repo root.
- Security policy: see [SECURITY.md](SECURITY.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome. For agent-driven contributors, see [AGENTS.md](AGENTS.md).

## License

MIT — see [LICENSE](LICENSE).

## About

Built by [Hermes Labs](https://hermes-labs.ai). Sealed with hermes-seal v1.

Related work: [lintlang](https://github.com/roli-lpci/lintlang) (static linter for AI agent code), [cogito-ergo](https://github.com/roli-lpci/cogito-ergo) (agent memory with integer-pointer fidelity), [claude-router](https://github.com/roli-lpci/claude-router) (scaffold router).

---

If this saved you the five minutes of eyeballing a fan-out's outputs, ⭐ the repo — it helps others find it.
