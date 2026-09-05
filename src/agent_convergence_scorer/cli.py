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
import math
import sys
from typing import Any

from agent_convergence_scorer import __version__
from agent_convergence_scorer.receipt import make_post_run_receipt
from agent_convergence_scorer.scorer import score_runs

THRESHOLD_NOT_MET_EXIT_CODE = 3


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


def _minimum_convergence(value: str) -> float:
    """Parse one finite convergence threshold in the public score range."""
    try:
        threshold = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a finite number in [0, 1]") from exc
    if not math.isfinite(threshold) or not 0.0 <= threshold <= 1.0:
        raise argparse.ArgumentTypeError("must be a finite number in [0, 1]")
    return threshold


def _normalize_minimum_convergence_argument(argv: list[str] | None) -> list[str]:
    """Let argparse validate negative non-finite values as threshold values.

    ``argparse`` treats ``-inf`` as another option rather than the value for
    ``--min-convergence``. Keep the normal command-line spelling useful by
    rewriting only those non-finite spellings to the equivalent ``--option=``
    form before the normal type validator runs.
    """
    normalized = list(sys.argv[1:] if argv is None else argv)
    negative_nonfinite = {"-inf", "-infinity", "-nan"}
    index = 0
    while index + 1 < len(normalized):
        is_negative_nonfinite = normalized[index + 1].lower() in negative_nonfinite
        if normalized[index] == "--min-convergence" and is_negative_nonfinite:
            normalized[index] = f"--min-convergence={normalized[index + 1]}"
            del normalized[index + 1]
        index += 1
    return normalized


def _receipt_main(argv: list[str]) -> int:
    """Run the separately versioned Hermes post-run receipt adapter."""
    parser = argparse.ArgumentParser(
        prog="agent-convergence-scorer receipt",
        description=(
            "Turn Hermes-shaped parallel agent-result JSON into a lexical "
            "convergence receipt. Decisions are review or investigate only."
        ),
    )
    parser.add_argument("input", help='JSON file (or "-" for stdin) with a results list')
    parser.add_argument(
        "--min-convergence",
        type=_minimum_convergence,
        default=0.7,
        metavar="FLOAT",
        help="lexical convergence threshold in [0, 1] (default: 0.7)",
    )
    parser.add_argument(
        "--indent", type=int, default=2, help="JSON indent (default: 2; 0 is compact)"
    )
    args = parser.parse_args(_normalize_minimum_convergence_argument(argv))
    try:
        payload = _load(args.input)
        receipt = make_post_run_receipt(payload, args.min_convergence)
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {args.input}: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: could not read {args.input}: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=args.indent if args.indent > 0 else None))
    if not receipt["minimum_convergence"]["passed"]:
        print(
            "error: lexical convergence is below the receipt minimum; investigate required",
            file=sys.stderr,
        )
        return THRESHOLD_NOT_MET_EXIT_CODE
    return 0


def main(argv: list[str] | None = None) -> int:
    normalized_argv = list(sys.argv[1:] if argv is None else argv)
    if normalized_argv and normalized_argv[0] == "receipt":
        return _receipt_main(normalized_argv[1:])
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
        "--min-convergence",
        type=_minimum_convergence,
        metavar="FLOAT",
        help=(
            "require an inclusive minimum reported convergence score: FLOAT "
            "must be finite in [0, 1]; equality passes. A failure exits 3, "
            "keeps JSON stdout valid, and writes a human-readable failure to stderr"
        ),
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indent for output (default: 2; use 0 for compact)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(_normalize_minimum_convergence_argument(normalized_argv))

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
    threshold_passed = True
    if args.min_convergence is not None:
        threshold_passed = result["convergence_score"] >= args.min_convergence
        result["minimum_convergence"] = {
            "threshold": args.min_convergence,
            "passed": threshold_passed,
        }

    indent = args.indent if args.indent > 0 else None
    print(json.dumps(result, indent=indent))
    if not threshold_passed:
        print(
            "error: convergence score "
            f"{result['convergence_score']} is below minimum {args.min_convergence}",
            file=sys.stderr,
        )
        return THRESHOLD_NOT_MET_EXIT_CODE
    return 0


if __name__ == "__main__":
    sys.exit(main())
