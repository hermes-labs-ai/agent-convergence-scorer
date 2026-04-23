"""Command-line interface for agent-convergence-scorer.

Entry point: `agent-convergence-scorer <input.json>` or `python -m agent_convergence_scorer`.

Input JSON may be either:
    {"runs": ["output 1", "output 2", ...]}
or:
    ["output 1", "output 2", ...]

Use `-` as the filename to read from stdin.

Exit codes:
    0 — scoring succeeded
    1 — input parse error (file missing, invalid JSON, wrong shape)
    2 — usage error (no input argument)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from agent_convergence_scorer import __version__
from agent_convergence_scorer.scorer import score_runs


def _load(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path) as f:
        return json.load(f)


def _extract_runs(data: Any) -> list[str]:
    runs = data.get("runs", data) if isinstance(data, dict) else data
    if not isinstance(runs, list) or len(runs) == 0:
        raise ValueError("input must be a non-empty list of strings (or {'runs': [...]})")
    if not all(isinstance(r, str) for r in runs):
        raise ValueError("all run entries must be strings")
    return runs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-convergence-scorer",
        description=(
            "Score how similar N agent outputs are. "
            "Produces exact-match rate, Jaccard token overlap, divergence point, "
            "and a composite convergence score in [0, 1]."
        ),
    )
    parser.add_argument(
        "input",
        help='JSON file (or "-" for stdin). Shape: ["run1","run2",...] or {"runs":[...]}',
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indent for output (default: 2; use 0 for compact)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        data = _load(args.input)
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON in {args.input}: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error: could not read {args.input}: {e}", file=sys.stderr)
        return 1

    try:
        runs = _extract_runs(data)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    result = score_runs(runs)
    indent = args.indent if args.indent > 0 else None
    print(json.dumps(result, indent=indent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
