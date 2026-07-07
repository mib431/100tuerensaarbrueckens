# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static photo gallery: "100 Türen Saarbrücken". 100 numbered slots (001..100), each one door photo with optional caption and EXIF GPS pin. Deployed as plain HTML on GitHub Pages — no build server, no JS framework.

## Pipeline (the core mental model)

Three stages, all idempotent:

```
raw/NNN.jpg ──process.py──> NNN.jpg (root) ──┐
                                              ├─ bake.py ──> gallery.html (DATA block + footer)
                              bottom.html ────┘
```

1. **`raw/NNN.jpg`** — originals, untouched. Filename rule is strict: zero-padded 3 digits, lowercase `.jpg`, range `001`–`100`. `bake.py` reads GPS EXIF from these only indirectly (it reads from the processed root JPGs, which preserve GPS).
2. **`process.py`** — reads `raw/`, writes processed copies to project root as `NNN.jpg`. Per-photo: EXIF orientation → vertical-line auto-straighten (Hough lines, clamped ±5°) → 4:5 center crop → NL-means denoise → unsharp mask → +15% saturation → resize long-edge ≤1600 px → save quality 88 with GPS preserved, orientation tag cleared. Mtime cache: only reprocesses when raw or `process.txt` is newer than output. Slow (~3-5 s/photo, denoise dominates).
3. **`bake.py`** — walks slots 1..100 at project root, reads GPS from each present `NNN.jpg`, merges with `descriptions.txt`, emits a `const DATA=[...]` JS array of length 100 (entries are `null` for missing slots, `{lat, lon, desc?}` otherwise). With `--inject gallery.html` it does **two** in-place replacements in one pass: the `DATA` block between `/*BEGIN*/.../*END*/`, and the page footer between `<!--BEGIN_BOTTOM-->...<!--END_BOTTOM-->` (content sourced from `bottom.html`).
4. **`gallery.html`** — single self-contained file. Inline CSS+JS, no dependencies. Parses `DATA`, renders 100 tiles (real or placeholder). 📍 link → OpenStreetMap. Click image → `<dialog>` lightbox with prev/next (buttons, wraps around, arrow keys) cycling through slots that have data. Footer (`#bottom`) hidden via `:empty` if `bottom.html` absent.

## Sidecar files

- **`descriptions.txt`** — captions. `NNN=text` per line, `#` comments, UTF-8. Caption for missing slot or for slot without GPS gets warning + dropped/rendered-without-pin (current code only drops when file missing; without-GPS still shows caption).
- **`process.txt`** — per-photo processing overrides: `NNN.field=value`. Fields: `rot` (manual deg), `no_rot` (skip auto-straighten), `crop` (top/center/bottom or `NN%`), `sharp` (0..2 multiplier), `sat` (0..2 multiplier), `denoise` (on/off). Editing this file bumps its mtime, which triggers reprocessing of all affected slots on next `process.py` run.
- **`bottom.html`** — raw HTML fragment (no `<html>`/`<body>` wrapper) injected into the page footer at bake time. Optional; missing → footer renders empty and is hidden by CSS. Inherits page styles, no isolation.

## Common commands

```powershell
pip install -r requirements.txt              # one-time: Pillow, opencv-python, numpy

python process.py                            # incremental: only changed/new raws
python process.py --force                    # rebuild all
python process.py --only 42 7 --force        # specific slots
python process.py --dry-run                  # log, write nothing

python bake.py                               # print DATA block to stdout
python bake.py --inject gallery.html         # rewrite gallery.html in place
python bake.py --dir <photo-dir>             # use different processed-photos dir
```

Preview: open `gallery.html` directly in browser (no server needed).

Deploy: `git push` to GitHub Pages, see `deploy.md`. Standard add-photo flow in `add_new.md`. Walking route plan for collecting all 100 doors: `route.md`. Phone capture / EXIF GPS injection: `mi12.md`. Custom domain registration + ongoing maintenance: `dns.md`.

## Important invariants when modifying

- **Filename rule is load-bearing.** Both scripts iterate `range(1, 101)` and look for exactly `f'{slot:03d}.jpg'`. Any other naming is invisible to the pipeline.
- **Two marker pairs in `gallery.html` are load-bearing:**
  - `/*BEGIN*/` / `/*END*/` (inside `<script>`) — wraps the `DATA` array. Must stay on one line; the array is JSON-rendered as a single token.
  - `<!--BEGIN_BOTTOM-->` / `<!--END_BOTTOM-->` (inside `<footer id="bottom">`) — wraps the footer fragment from `bottom.html`. May span lines.
  Both pairs use a shared `inject()` driver in `bake.py` keyed by exact begin/end strings; removing, renaming, or duplicating any marker breaks the bake.
- **GPS is read from the *processed* root JPG, not from `raw/`.** `process.py` preserves the GPS EXIF block while clearing the orientation tag (writes orientation=1). If you change `process.py` to drop EXIF, `bake.py` will produce all-pin-less tiles.
- **The mtime cache assumes only `process.txt` is the global trigger.** If you add another sidecar that affects processing, plumb it through `needs_rebuild()` or runs become silently stale.
- **`gallery.html` is self-contained on purpose** (single file, no external CSS/JS, no fonts, no map tiles). Map "pin" is just an OpenStreetMap deep link, not an embedded map. Keep it that way unless explicitly asked.
- **Idempotency.** Re-running `process.py` and `bake.py` on unchanged inputs must be a no-op (or near-no-op). Don't introduce timestamps or random IDs into output.

## Architecture notes

- No tests, no linter, no CI configured. Validation is by running the pipeline and eyeballing `gallery.html`.
- No package manager beyond `pip` + `requirements.txt`. No `venv` checked in.
- `raw/` directory may contain large originals; `deploy.md` notes they're committed (option 1) — fine for 100-photo scale, well under GitHub's 1 GB soft cap.
- Windows-first dev environment. All docs use PowerShell + Windows paths. Scripts themselves are platform-neutral Python.
