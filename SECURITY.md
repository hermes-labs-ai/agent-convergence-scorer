# Security Policy

## Supported versions

Only the latest released version receives security fixes.

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a vulnerability

Please do **not** open a public GitHub issue for security reports.

Email `rbosch@lpci.ai` with subject `[security] agent-convergence-scorer`. You can expect an acknowledgement within 5 business days.

For coordinated disclosure, include:

- a minimal reproducer (input JSON + command)
- affected version
- observed vs expected behavior
- your disclosure timeline preference

## Attack surface

This package:

- reads a JSON file from disk (or stdin) and parses it with the Python stdlib `json` module
- performs pure-Python string and set operations on the resulting list of strings
- writes a JSON document to stdout

It does **not**:

- make network requests
- execute user-provided code
- shell out to subprocesses
- read or write files beyond the explicit `input` argument
- handle credentials, tokens, or secrets

The realistic threat model is therefore limited to: (a) JSON parser resource exhaustion (pathological input), (b) memory pressure from enormous input strings, and (c) bugs in the arithmetic on floats. The package has no privileged runtime state.

## Supply chain

- The repository is sealed with [hermes-seal](https://github.com/roli-lpci/hermes-seal) v1. Verify with `hermes-seal verify <path>`.
- SBOM at `sbom.cdx.json` (CycloneDX 1.5).
- Zero runtime dependencies — the SBOM lists only the package itself.

## History

No security vulnerabilities have been disclosed against this project.
