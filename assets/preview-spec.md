# Preview asset spec — agent-convergence-scorer

One static terminal-style image used for the GitHub social preview and the README banner. Consistent with the shared Hermes Labs micro-tool preview format.

## Format

- **Type:** static PNG (no GIF, no video)
- **Dimensions:** 1280 × 640 px (GitHub social-preview recommended 1280×640; also fits PyPI readme width)
- **DPI:** 144 (retina-sharp on PyPI)
- **Background:** flat `#0f172a` (slate-900)
- **Padding:** 48 px inside the frame
- **Font:** `JetBrains Mono` (or `Menlo` / `Monaco` fallback), 18 px, anti-aliased
- **Line height:** 1.45
- **Terminal chrome:** three macOS-style dots in the top-left (red `#ff5f56`, yellow `#ffbd2e`, green `#27c93f`), 12 px each, 8 px spacing, 32 px from top edge
- **Window title (centered under dots):** `agent-convergence-scorer` in `#94a3b8`
- **Prompt glyph:** `$ ` in `#38bdf8` (sky-400)
- **Command text:** `#e2e8f0` (slate-200)
- **JSON keys:** `#7dd3fc` (sky-300)
- **JSON strings:** `#a7f3d0` (emerald-200)
- **JSON numbers:** `#fde68a` (amber-200)
- **Brackets / punctuation:** `#94a3b8` (slate-400)

## Source content

The source text for the terminal window is `preview-source.txt` in this directory. It is **real CLI output** captured with:

```bash
echo '{"runs": ["The capital is Paris.", "The capital is Paris.", "The capital is Lyon."]}' \
  | agent-convergence-scorer -
```

No synthetic output. No fake results. No "Starring customers" cards.

## Generation

Two acceptable paths:

1. **Automated** — `carbon-now-cli` or `freeze` (charmbracelet/freeze) pointed at `preview-source.txt`. Command for `freeze`:
   ```bash
   freeze --language=bash --config=hermes.json --output=assets/preview.png assets/preview-source.txt
   ```
   A `hermes.json` config encoding the values above is a small one-time effort; share it across all Hermes Labs micro-tools.

2. **Manual** — open `preview-source.txt` in a terminal with the colors above, screenshot at 1280×640, save as `assets/preview.png`.

## Reuse across future Hermes Labs micro-tools

This same spec is the standard:

- Same dimensions (1280×640).
- Same slate-900 background.
- Same JetBrains Mono / 18 px / 1.45 line-height.
- Same three-dot chrome and centered tool-name title.
- Always real CLI output, never a stock screenshot or mock UI.
- Filename is always `assets/preview.png`, source is always `assets/preview-source.txt`.

When another Hermes Labs micro-tool launches, copy this `preview-spec.md` verbatim and only update the `preview-source.txt` content.

## Status

- `preview-source.txt` — ✅ present (real output)
- `preview.png` — ⏳ to be generated at push time. The binary is not committed yet; generating it requires the `freeze` CLI or equivalent. Tracked in `CHANGELOG.md` under `[Unreleased]` once generated.
