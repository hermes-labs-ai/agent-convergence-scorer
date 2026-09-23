<div align="center">

<h1>agent-convergence-scorer</h1>

agent-convergence-scorer is a CLI and Python library that scores how lexically similar N agent outputs are — exact-match rate, Jaccard token overlap, divergence point, and a composite 0–1 convergence score over any list of agent runs.

agent-convergence-scorer is developed by [Hermes Labs](https://hermes-labs.ai).

Hermes Labs is an agentic infrastructure company building the reliability layer for autonomous systems.

[![PyPI](https://img.shields.io/pypi/v/agent-convergence-scorer.svg)](https://pypi.org/project/agent-convergence-scorer/)
[![Python](https://img.shields.io/pypi/pyversions/agent-convergence-scorer.svg)](https://pypi.org/project/agent-convergence-scorer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/hermes-labs-ai/agent-convergence-scorer/actions/workflows/ci.yml/badge.svg)](https://github.com/hermes-labs-ai/agent-convergence-scorer/actions/workflows/ci.yml)

</div>

Comparison is whitespace-lexical, not semantic (see [When not to use it](#when-not-to-use-it)).

## Post-run receipt for parallel agents

For a thin, provider-independent post-run integration, the `receipt` command
accepts structured parallel-agent results and emits a separately versioned
machine-readable receipt. Its only decisions are `review` and `investigate`;
`acceptance_authority` is always `false`.

```bash
agent-convergence-scorer receipt --min-convergence 0.6 examples/hermes_parallel_results.json
```

Input must contain at least two results with unique non-empty `agent_id` values
and string `output` fields. Extra metadata may remain in the upstream record:

```json
{"results": [{"agent_id": "research-a", "output": "..."}, {"agent_id": "research-b", "output": "..."}]}
```

A passing threshold exits `0` and returns `review`; an unmet threshold still
prints valid JSON, returns exit `3`, and returns `investigate`. Use the minimum
only for expected reproducibility across same-task reruns. Do not use high
convergence as success for ideation or diversity work, where convergence can
instead indicate collapse. The receipt is lexical-output evidence only: it does
not establish semantic agreement, correctness, or permission to accept, merge,
deploy, or skip tests/review.

Use this when repeated runs of the same task return short, canonical answers and
you need to spot output instability before it reaches users. It also exposes
verbatim and lexical duplication in a fan-out. It cannot tell whether different
wording expresses the same idea.

## Pain

- Your eval harness reports accuracy but not run-to-run stability for the same prompt.
- A classifier or router sometimes changes its short answer across repeated calls.
- A fan-out may be returning duplicate wording when you expected independent outputs.
- A temperature or prompt change needs a consistent lexical comparison across runs.
- You need to see whether short, canonical answers from repeated runs are stable.

## Install

```bash
python -m pip install agent-convergence-scorer
```

Or install the CLI from the [Hermes Labs Homebrew tap](https://github.com/hermes-labs-ai/homebrew-tap):

```bash
brew install hermes-labs-ai/tap/agent-convergence-scorer
```

Python 3.9+. Zero runtime dependencies (stdlib only).

Confirm the install and see which version is active:

```bash
agent-convergence-scorer --version
```

This prints the installed console script's version.

## Quick start

```bash
echo '{"runs": ["The capital is Paris.", "The capital is Paris.", "The capital is Lyon."]}' \
  | agent-convergence-scorer -
```

Output:

```json
{
  "num_runs": 3,
  "exact_match_rate": 0.333,
  "token_metrics": {
    "avg_overlap": 0.733,
    "jaccard": 1.0
  },
  "convergence_score": 0.536,
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

### GitHub Action

Use the repository action to score JSON from your eval job in a workflow. It
installs this package from the action checkout, runs the same CLI, and exposes
the reported lexical `convergence_score`, `exact_match_rate`, and runner-local
`result_path` as outputs.

```yaml
- name: Produce repeated outputs for one prompt
  run: python scripts/run_eval.py > runs.json # replace with your eval command
- id: convergence
  uses: hermes-labs-ai/agent-convergence-scorer@v0.3.0
  with:
    input: runs.json
    min-convergence: "0.7"
```

A supplied `min-convergence` is inclusive. Calibrate it on repeated outputs
from the same task and compare short canonical results, such as labels or
normalized JSON fields. The action does not run your agents; it scores the
`{"runs": ["...", "..."]}` file your eval job produces. If the score is lower,
the action still writes valid result JSON and exits `3`; it does not treat
lexical convergence as correctness or approval of the underlying runs.

Interpret:

- `convergence_score = 0.536` — partial lexical consistency, not a correctness score.
- `exact_match_rate = 0.333` — 1 of the 3 run pairs is byte-identical.
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
# {'num_runs': 3, 'exact_match_rate': 0.0,
#  'token_metrics': {'avg_overlap': 0.6, 'jaccard': 0.6},
#  'convergence_score': 0.33,
#  'divergence_point': {'diverges_at_token': 'a', 'token_position': 3, 'num_tokens_to_divergence': 3}}
```

Individual metrics are importable too: `exact_match_rate`, `token_overlap`, `divergence_point`, `convergence_score`, `tokenize`.

## Metrics — what they mean

| Metric | Range | What it measures |
|---|---|---|
| `exact_match_rate` | `[0, 1]` | Fraction of all run pairs with byte-identical outputs. Unaffected by run order. |
| `token_metrics.jaccard` | `[0, 1]` | Token-set Jaccard of the first two runs (quick eyeball). |
| `token_metrics.avg_overlap` | `[0, 1]` | Mean Jaccard over all `C(N,2)` pairs. Robust to N. |
| `divergence_point.num_tokens_to_divergence` | `[0, min_len]` | First position where runs disagree. Late divergence = strong shared prefix. |
| `convergence_score` | `[0, 1]` | Order-independent composite: `0.5 * exact_match + 0.3 * avg_overlap + 0.2 * div_distance_norm`. |

## When to use it

- Quick lexical consistency check for repeated short answers to the same task.
- CI gate: fail if N reruns of a prompt drop below a calibrated threshold.
- Measuring the effect of a temperature, prompt, or framing change on lexical output stability.
- Finding verbatim or lexically similar duplicates in a multi-agent fan-out.

## When not to use it

- **Semantic similarity.** Tokenization is whitespace-only; "Paris, France" and "paris, france," are different token sets. If you need meaning-level comparison, pair these metrics with a sentence-embedding similarity (or a reranker) externally.
- **Freeform ideation collapse or factual correctness.** Different prose can
  express the same idea, and identical wrong answers can score `1.0`.
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

## Example: flagging unstable short answers

```python
from agent_convergence_scorer import score_runs

# Collect one canonical answer from each repeat of the same task.
runs = ["approve", "approve", "reject"]
result = score_runs(runs)

print(result["exact_match_rate"])   # 0.333: one matching pair of three
print(result["convergence_score"])  # 0.266: investigate this run set
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

[Hermes Labs](https://hermes-labs.ai) is an agentic infrastructure company building the reliability layer for autonomous systems. We find the structural AI failures standard evals miss, then harden retrieval, memory, agents, and the language layers around production AI systems with runtime controls and defensible evidence.

Browse the [open-source catalog](https://hermes-labs.ai/open-source) or contact [roli@hermes-labs.ai](mailto:roli@hermes-labs.ai).

---

If this saved you the five minutes of eyeballing a fan-out's outputs, ⭐ the repo — it helps others find it.
