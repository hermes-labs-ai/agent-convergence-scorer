# Contributing

Thanks for your interest. This is a small, focused utility — it is intentionally narrow, and we plan to keep it that way.

## Scope

**In-scope:** bug fixes, additional lexical metrics, better input validation, better error messages, docs improvements, test coverage.

**Out-of-scope:**

- Semantic metrics that would add a runtime dependency (embeddings, rerankers). A companion package is welcome — open an issue first.
- Subword / BPE tokenization.
- Network I/O of any kind.
- Anything that changes the output schema without a major-version bump.

If you're not sure, open an issue before writing code.

## Development setup

```bash
git clone https://github.com/hermes-labs-ai/agent-convergence-scorer
cd agent-convergence-scorer
python -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Running the checks

```bash
ruff check .
pytest -ra
```

CI runs the same commands on Python 3.9–3.13 across Linux, macOS, and Windows. If it passes locally, it should pass in CI; if not, please report which step diverged.

## Pull request checklist

- [ ] `ruff check .` passes
- [ ] `pytest -ra` passes
- [ ] No new runtime dependency was added (`[project.dependencies]` stays empty)
- [ ] `CHANGELOG.md` has a new entry under `[Unreleased]`
- [ ] Tests added for any new behavior; existing tests still pass
- [ ] No backward-incompatible schema change without a major-version bump

## Filing issues

Use the templates at `.github/ISSUE_TEMPLATE/`. Minimum useful bug report: Python version, OS, exact command or code snippet, the JSON input, the observed output, the expected output.

## Code of conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Contributor Covenant 2.1.

## License

By contributing, you agree that your contributions are licensed under the MIT License (see [LICENSE](LICENSE)).
