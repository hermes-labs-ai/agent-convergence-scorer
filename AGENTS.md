# AGENTS.md — agent-convergence-scorer

Instructions for AI agents contributing to or using this tool.

## What this tool does

Takes a list of N strings (each string = one agent run on the same prompt) and returns four numbers:

- `exact_match_rate ∈ [0, 1]` — fraction identical to `runs[0]`
- `token_metrics.avg_overlap ∈ [0, 1]` — mean pairwise Jaccard over whitespace tokens
- `divergence_point.num_tokens_to_divergence ∈ [0, min_len]` — first disagreement position
- `convergence_score ∈ [0, 1]` — composite, weights `0.5 * exact_match + 0.3 * avg_overlap + 0.2 * div_distance_norm`

Zero runtime dependencies. Python 3.9+. CLI and library both supported.

## When to use

- You ran N agents on the same prompt and want one number for how much they agreed.
- You want a CI gate that fails when reruns of a prompt drop below a convergence threshold.
- You are running a multi-agent hackathon or fan-out and want to measure ideation collapse.
- You need a downstream metric for a temperature/prompt/framing A/B test.

## When NOT to use

- **Semantic similarity.** This is lexical only. Same meaning, different words → low score. Pair with an embedding model if you need semantics.
- **Subword / BPE / WordPiece comparisons.** Whitespace tokenization only.
- **Non-whitespace-segmented languages.** Tokenize upstream and pass the tokenized-then-joined form.
- **Ranking quality.** Use `ir-measures` or `ranx`.
- **Streaming / incremental scoring.** This is batch only.

## Minimal invocation — library

```python
from agent_convergence_scorer import score_runs
result = score_runs(["run 1 output", "run 2 output", "run 3 output"])
```

Returns:

```python
{
  "num_runs": 3,
  "exact_match_rate": 0.333,
  "token_metrics": {"avg_overlap": 0.42, "jaccard": 0.5},
  "convergence_score": 0.413,
  "divergence_point": {"diverges_at_token": "output", "token_position": 1, "num_tokens_to_divergence": 1}
}
```

## Minimal invocation — CLI

```bash
echo '{"runs": ["a", "a", "b"]}' | agent-convergence-scorer -
```

or:

```bash
agent-convergence-scorer input.json
```

Input JSON may be either `["run1", "run2", ...]` or `{"runs": ["run1", ...]}`.

Exit codes:

- `0` — success
- `1` — input error (missing file, invalid JSON, wrong shape, non-string elements)
- `2` — usage error (argparse built-in)

Stderr is a single human-readable error line on non-zero exit; stdout is empty on error. No stacktrace leaks.

## Expected output shape

```json
{
  "num_runs": <int>,
  "exact_match_rate": <float 0..1>,
  "token_metrics": {
    "avg_overlap": <float 0..1>,
    "jaccard": <float 0..1>
  },
  "convergence_score": <float 0..1>,
  "divergence_point": {
    "diverges_at_token": <string or null>,
    "token_position": <int>,
    "num_tokens_to_divergence": <int>
  }
}
```

All float fields round to 3 decimal places.

## Known limitations

- Tokenizer is `str.lower().split()`. Punctuation becomes part of tokens (`"Paris."` ≠ `"Paris"`).
- Composite weights (50/30/20) are heuristic, not learned.
- `divergence_point` walks up to `min(len(tokenize(r)) for r in runs)` — if one run is much shorter, the divergence search is capped by the shortest.
- `token_overlap.jaccard` is the *first two runs only* (legacy eyeball metric). Prefer `avg_overlap` for N > 2.
- No semantic understanding.

## Common failure cases

| Input | Behavior |
|---|---|
| `[]` (empty list) | exit 1, stderr `"error: input must be a non-empty list of strings"` |
| `[1, 2, 3]` (non-strings) | exit 1, stderr `"error: all run entries must be strings"` |
| Missing file | exit 1, stderr `"error: file not found: <path>"` |
| Malformed JSON | exit 1, stderr `"error: invalid JSON in <path>: <reason>"` |
| Single-run list `["only"]` | convergence_score = 1.0 (trivially), no error |

## What counts as success when contributing

Any PR must:

1. Pass `pytest` locally and in CI.
2. Pass `ruff check` locally and in CI.
3. Not add a runtime dependency (`[project.dependencies]` stays empty). Dev-only deps go in `[project.optional-dependencies.dev]`.
4. Not change the existing metric names, ranges, or output schema without a major-version bump.
5. Not add semantic/embedding logic inside this package — that's a downstream composition, not this tool's job. A separate companion package is welcome.
6. Update `CHANGELOG.md` under an `[Unreleased]` section.

## Trust

- Staged `hermes-seal` v1 manifest at `.hermes-seal.yaml`. Signature is granted out-of-band by the Hermes Labs internal sealing toolchain.
- SBOM at `sbom.cdx.json` (CycloneDX 1.5).
- Zero runtime deps by design — the SBOM lists only the package itself.

## Origin

Extracted from a prototype built during the Hermes Labs Cascade Hackathon on 2026-04-22. Full experiment writeup is in the Hermes internal research corpus; the public summary is in the [CHANGELOG](CHANGELOG.md#010--2026-04-22).

## About Hermes Labs

[Hermes Labs](https://hermes-labs.ai) builds AI audit infrastructure for enterprise AI systems — EU AI Act, ISO 42001, agent-level risk. We open-source the tools we use internally. Everything is MIT, fully free, no SaaS tier. Audit work is paid; the code is not.

Companion OSS to consider pairing with this scorer:
- **[lintlang](https://github.com/hermes-labs-ai/lintlang)** — static linter for agent configs
- **[hermes-jailbench](https://github.com/hermes-labs-ai/hermes-jailbench)** — jailbreak regression benchmark
- **[little-canary](https://github.com/hermes-labs-ai/little-canary)** — prompt-injection detection
- **[claude-router](https://github.com/hermes-labs-ai/claude-router)** — model-tier + scaffold router

Full stack listed in the repo README.
