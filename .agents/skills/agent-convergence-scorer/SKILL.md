---
name: agent-convergence-scorer
description: Use when you ran the same prompt through N agents or LLM calls and need a number for whether the outputs are N distinct answers or have collapsed to one — exact-match rate, Jaccard token overlap, divergence point, and a composite 0-1 convergence score. Lexical (whitespace-token) comparison, not semantic. Zero dependencies, no MCP.
license: MIT
compatibility: Requires Python 3.9+; installs via pip. Zero runtime dependencies (stdlib only).
---

# agent-convergence-scorer

agent-convergence-scorer is a CLI and Python library that scores how
lexically similar N agent or LLM outputs are: exact-match rate, Jaccard token
overlap, divergence point, and a composite convergence score over any list of
runs. Comparison is whitespace-lexical, not semantic.

## Use it for

- Scoring whether a fan-out of N parallel agents converged on the same answer
  or produced N distinct outputs
- A CI gate that fails a job when reproducibility across same-task reruns
  drops below a threshold (`--min-convergence`)
- A post-run receipt for structured parallel-agent results with `agent_id`
  and `output` fields (`receipt` subcommand)
- Measuring the effect of a temperature, prompt, or framing change on output
  stability

## Do not use it for

- Semantic similarity — tokenization is whitespace-only, so "Paris, France"
  and "paris, france," are different token sets
- High convergence as a success signal for ideation/diversity work, where
  convergence can instead indicate collapse
- Ranking quality (nDCG, MRR) or subword/BPE tokenization studies

## Quickstart

```bash
pip install agent-convergence-scorer
echo '{"runs": ["The capital is Paris.", "The capital is Paris.", "The capital is Lyon."]}' \
  | agent-convergence-scorer -
```

CI threshold gate:

```bash
printf '%s\n' '{"runs": ["same output", "same output"]}' \
  | agent-convergence-scorer --min-convergence 1.0 -
```

Post-run receipt for parallel-agent results:

```bash
agent-convergence-scorer receipt --min-convergence 0.6 examples/hermes_parallel_results.json
```

## Output shape

- Default: JSON with `num_runs`, `exact_match_rate`, `token_metrics`
  (`avg_overlap`, `jaccard`), `convergence_score`, and `divergence_point`
- With `--min-convergence`: adds `minimum_convergence: {threshold, passed}`;
  exits `0` when the score meets the threshold, `3` when it does not
- `receipt`: emits `decision` of `review` or `investigate`; always
  `acceptance_authority: false`

## Common gotchas

- All scoring functions reject an empty runs list with `ValueError` — no
  runs is not evidence of convergence.
- Invalid `--min-convergence` values (NaN, infinity, outside `[0, 1]`) are
  argparse usage errors with exit code `2`, distinct from the threshold-fail
  exit `3`.
- `receipt` requires at least two results with unique, non-empty `agent_id`
  values and string `output` fields.
- The composite weights (50% exact-match, 30% avg overlap, 20% divergence
  distance) are heuristic; call the individual functions directly to use
  your own weighting.

## More

Full docs and CLI reference:
https://github.com/hermes-labs-ai/agent-convergence-scorer
