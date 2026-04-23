# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-22

Initial public release.

### Added
- `score_runs(runs)` — compute all four metrics in one call
- `exact_match_rate(runs)` — fraction of runs identical to `runs[0]`, range `[0, 1]`
- `token_overlap(runs)` — pairwise Jaccard over whitespace tokens
- `divergence_point(runs)` — first token position where runs disagree
- `convergence_score(runs)` — composite 0-1 score, weights `0.5 * exact_match + 0.3 * avg_token_overlap + 0.2 * normalized_divergence_distance`
- `agent-convergence-scorer` CLI — reads JSON from file or stdin, emits JSON results
- Stdin input support via `-` argument
- Stdlib-only — no runtime dependencies
- Python 3.9+ support

### Origin
Extracted and hardened from a prototype built during the Hermes Labs
Cascade Hackathon (2026-04-22), a controlled experiment measuring whether
prompt framing affects ideation convergence across N concurrent agents.
The scorer provided the method by which that experiment measured collapse.

[0.1.0]: https://github.com/roli-lpci/agent-convergence-scorer/releases/tag/v0.1.0
