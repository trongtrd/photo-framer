# Handoff: Photo Framer upgrade roadmap

Last updated: 2026-11-05.
Owner: project owner (writes in Vietnamese; reply in Vietnamese, use photography/post-processing terms).

## Status

- **Phase 0**: branch `claude/happy-ptolemy-vpmy5z` (style H, portrait demo, this handoff) is open as PR trongtrd/photo-framer#1 into `main` (awaiting owner review).
- **Phase 1 implemented** on branch `claude/tender-lovelace-j9q91m`, stacked on `claude/happy-ptolemy-vpmy5z` (rebase onto `main` once #1 merges). Output verified byte-identical with `tools/golden.py compare --base 97c89fc`.
- **Phase 2 implemented** on branch `claude/phase2-metadata`, stacked on phase 1 (owner choices: `--metadata keep|strip`; C shows `α7C` beside the logo, D `Sony α7C`; one flag per typed field). Phase 3 implemented on branch `claude/phase3-minimal-mat`, stacked on phase 2 (owner-approved: margins 3:4 4.0% / 9:16 5.0%, shares 1080×1440 / 1080×1920, blur darkened ~12% by default with `--blur-tone`). Next: phase 4.

## Where to read first (do not duplicate here)

| Topic | Source |
|---|---|
| What the project is, user-facing styles A–H, CLI usage, technical limits, demo reproduction | `README.md` |
| Agent behaviour rules (no invented text, crop only with approval, verification, delivery) | `skills/photo-framer/SKILL.md`; per-style rules in `references/styles/` |
| Per-style menus (VI/EN) and geometry constants | `skills/photo-framer/references/menus.md`, `references/presets.md` |
| Renderer | package `skills/photo-framer/scripts/photoframer/` (styles in `styles/`, registry in `registry.py`, `Settings` + flag matrix in `settings.py`); CLI entry `scripts/frame_photo.py` |
| Regression tests (38 tests, unittest, synthetic images) | `skills/photo-framer/scripts/test_frame_photo.py` — run `python skills/photo-framer/scripts/test_frame_photo.py` |
| CI matrix (Ubuntu/Windows/macOS, Python 3.10/3.12, Pillow 10.1–12.x) | `.github/workflows/test.yml` |
| Commit history of this session | `git log 6408659..HEAD` (`bf39038` style H, `3cc621f` portrait examples) |

## What this session delivered

1. **Style H — Minimal Mat** (commit `bf39038`): code `1-1-1` default; rows = canvas ratio (4:5 / 1:1 / follow photo with thin border) – mat (white / warm light gray `#EBE5E5` / ivory) – black keyline (thin / none / thick). Photo is always fitted whole, centered, never scaled or cropped; `--share` gives exact 1080×1350 / 1080×1080 for 4:5 / 1:1. Function `minimal_mat_geometry()` in `frame_photo.py`. Added to `--preview` (filename now `_ABCEFGH_preview` / `_ABCDEFGH_preview`). Docs, menus, presets, `agents/openai.yaml`, workflow SVGs updated.
2. **Portrait demo** (commit `3cc621f`): owner-supplied Prague photo `docs/images/demo-portrait-source.jpg` (1000×1500, no EXIF/GPS; owner explicitly authorised publishing it) plus `demo-portrait-h-4x5.jpg`, `-1x1.jpg`, `-thin.jpg` and a README section "Portrait photos in style H".
3. **Competitive research** on GitHub (results were given in chat only). The relevant repos, for re-checking ideas: `leslievan/semi-utils`, `dearDreamWeb/camera-watermark` (blur background), `HNagouda/autopost` (ratios incl. 3:4/9:16, blur, carousel, phone preview), `hexergogo/lenscript` (camera display names, keep EXIF), `JanoAngulo/edgeprint`, `musnows/framesign-miniprogram` (PNG signature), `akostm/bordermagick` (gallery wall label, layout files), `LordAmit/borderify` (JSON presets). The Photo Framer is the only one found that is packaged as an AI skill.

### Lesson learned (important)
When testing portrait input I cropped the landscape demo into a portrait test file without saying so; the owner thought the renderer cropped photos. **Never crop or alter an owner photo to create test data without stating it explicitly**, and prefer real full images (now available: the Prague portrait). The owner is strict: photo content must stay intact and is never cropped without approval.

The owner's three reference mockups for H (4:5 + keyline, 1:1 gallery card with title/subtitle, thin white border) existed only in the old session's temp folder; they are **not** in the repo. Measured facts from them are already encoded in `presets.md` (H section). The 1:1 reference had a centered two-line label under the photo: bold serif title + light gray sans subtitle, photo shifted up; this is the basis for task 4b.

## Decisions agreed with the owner (binding)

- **No new styles** for the upgrades below. Keep A–H. New layout geometry is the only reason to add a style.
- **Three-digit codes are a frozen contract**: never change the meaning of an existing code. New options are **named flags** (e.g. `--ratio 9:16`, `--background blur`, `--title`). Each feature declares which styles accept it; invalid combinations raise a clear error (same pattern as `--left-text` being F-only).
- **Refactor first** (phase 1) before any new feature, with byte-identical output.
- **Metadata default = keep EXIF including GPS** in output files; drop only the rest (see task 2c). **No warning, no extra question** about GPS.
- **Camera display names**: approved (e.g. `ILCE-7C` → `Sony α7C`).
- **9:16 / large outputs**: raise the output limit for style H (proposal: 100 MP; current global `MAX_OUTPUT_PIXELS = 60_000_000`). Final images are still never downscaled.
- **Blur background**: approved; blur a downscaled copy then upscale for speed; blur stays outside the photo.
- Tone: answer in Vietnamese; ask with `AskUserQuestion` and give a recommended option when a real decision is needed; otherwise proceed.

## Next tasks, in order

Each phase = its own commit series and its own PR; keep tests green on the CI matrix; update `CHANGELOG.md`, docs and demo images in the same PR. Do not create PRs unless the owner asks (they asked for the plan; ask before opening the first PR).

### Phase 0 — Close out H
- Ask the owner whether to open the PR for branch `claude/happy-ptolemy-vpmy5z` (style H + portrait demo + this handoff). If the PR was merged in the meantime, start the next phase from the updated default branch (keep the branch name, rebase/restart per repo rules).

### Phase 1 — Foundation refactor (v0.8, no behaviour change)
Goal: maintainability. Output must be **byte-identical** for every style and every choice code.

1. **Golden lock first**: before moving any code, write a script/test that renders every style × all 27 choice codes (plus D/F text variants, E fixed color, captions, `--share`, `--preview`) on a few synthetic images (landscape, portrait, square, tiny, profiled/alpha cases already used in tests) and records SHA-256 of outputs. After refactor, hashes must match exactly.
2. **Split `frame_photo.py` into a package**, keeping `scripts/frame_photo.py` as the thin CLI entry (SKILL.md and README reference that path):
   ```
   scripts/photoframer/
     io.py         load_photo, save_verified (atomic hard-link, no overwrite, pixel check)
     metadata.py   read_capture_metadata, format_specs, display_model, brand mapping
     color.py      ICC helpers (colors_in_profile), Color Echo
     text.py       fonts (specs_fonts, wordmark_font), text fitting rules
     components/   shadow, keyline, spec band, deckle paper, film border, backgrounds
     styles/       one module per style A–H, each declaring: code, names (VI/EN),
                   menu rows/options/defaults, accepted flags, geometry + render
     registry.py   ordered style registry used by CLI, preview and docs generator
   ```
   Keep a single source for constants currently at the top of `frame_photo.py`. Tests import via `importlib` from `frame_photo.py`; keep that working or update the import in `test_frame_photo.py`.
3. **Settings object**: replace positional `render(photo, style, code, caption, font_path, meta, right_text, frame_color, profile, echo_colors, left_text)` with a dataclass (style, choices, named options). This is what makes named flags scalable.
4. **Docs generation**: a script (e.g. `skills/photo-framer/scripts/gen_docs.py`) that writes the menu tables in `references/menus.md` and the style table in `README.md` between marker comments, from the registry. Add a test that fails when docs are stale.
5. **Compatibility matrix**: table (generated) of which named flags work with which styles; enforce in code.
6. **Slim `SKILL.md`** (progressive disclosure): keep routing + global rules; move per-style sections (C/D, E, F, G, H) to `references/styles/<style>.md` and link them. SKILL.md must stay accurate for agents in ChatGPT/Codex (`agents/openai.yaml`).
7. Split tests into per-area files under `scripts/tests/` or keep one runner; CI command in `.github/workflows/test.yml` must be updated if the path changes. Add `CHANGELOG.md` (history: v0.1 A/B … v0.6 G, v0.7 H, v0.8 refactor) and a version constant.

### Phase 2 — Metadata layer (v0.9)
a. **Manual capture details** for files without EXIF (film scans) or overrides: named flags such as `--camera`, `--lens`, `--iso`, `--aperture`, `--shutter`, `--focal` (or one `--specs` JSON/sidecar for batches). User-supplied values win over EXIF/XMP; JSON notes must say which fields came from the user. Applies to C/D (and the gallery label of phase 4). Never fill values the user did not give.
b. **Camera display names**: data file (e.g. `assets/cameras.json`: make + EXIF model → display name), only names verified against manufacturer naming; keep the raw model in JSON notes (`Model display formatted: 'ILCE-7C' -> 'Sony α7C'`, extending the current `display_model()` note); flag to disable (e.g. `--raw-model`). Brand logo already shows the make — avoid duplicating "Sony" next to the SONY logo in C (decide display form per style; ask owner if unclear).
c. **Output metadata** `--metadata keep|strip` (name to be finalised), **default keep**: copy EXIF from the source into final PNG (eXIf) and share JPEG **including GPS**; set Orientation = 1 (pixels are already transposed), update pixel dimensions, drop embedded thumbnail, MakerNote and XMP edit history. `strip` = current behaviour. No GPS warning (owner decision). Update README "Output metadata" bullet and SKILL.md line "Original EXIF/GPS metadata is excluded" — this is a deliberate behaviour change; record it in CHANGELOG. Tests: synthetic EXIF with GPS IFD, verify kept tags, Orientation=1, no thumbnail; `strip` removes everything.

### Phase 3 — Style H extensions (v0.10)
a. `--ratio 4:5|1:1|3:4|9:16|original` (named; menu row 1 keeps 1=4:5, 2=1:1, 3=original). Add minimum-margin and share sizes for new ratios (proposal: 3:4 → 1080×1440, 9:16 → 1080×1920; margins to agree with owner). Canvas width rounding must keep the ratio exact (see `minimal_mat_geometry`).
b. Raise output limit for H (proposal 100 MP) while keeping 60 MP for other styles; check memory; update docs/tests (current test asserts a 60 MP error for H with 6600×4400 — adjust).
c. `--background blur` (overrides menu row 2): fill canvas with the photo scaled to cover, blurred on a downscaled copy then upscaled, optional slight darken/lighten; photo pasted last and byte-verified; keyline still applies. Works in the source colour space (no ICC conversion needed). Consider later enabling for A/G via the compatibility matrix.

### Phase 4 — Text and overlays (v0.11)
a. **Slot system**: each style exposes free regions outside the photo (e.g. H bottom/top margin, C/D band, A/G margins). Text/overlays request a slot; if it does not fit → error asking for shorter text or wider margin. Never draw over the photo.
b. **Gallery label**: `--title` / `--subtitle` (exact wording, one line each, ≤200 chars, Vietnamese accents preserved). Bundle an OFL serif with Vietnamese glyphs (e.g. Noto Serif) in `assets/fonts/` with licence file. In H fixed ratios, shift the photo up to make room below (as in the owner's 1:1 reference). Decide whether existing `--caption` maps onto this (keep backward compatibility).
c. **PNG signature/logo**: `--signature path.png` with placement options within slots (e.g. bottom-right/bottom-center), size relative to canvas, opacity; keep transparency; error if it would touch the photo.

## Practical notes for the next agent
- Adding a named flag: add a `Settings` field and an `Option` in `photoframer/settings.py`, list it in each accepting style's `accepts` (and `requires` if mandatory), add the CLI argument in `photoframer/cli.py`, then run `python tools/gen_docs.py`. The matrix test fails if enforcement and declarations disagree.
- Refactors: run `python tools/golden.py compare --base <rev>` before committing; it takes ~1.5 min. Hashes are machine-specific, so it compares two code versions on the same machine instead of storing hashes.
- Known pre-existing quirk (not changed in phase 1, since output must stay identical): outputs that embed the renderer's generated sRGB profile (unprofiled inputs, previews, share JPEGs) carry the LittleCMS creation timestamp, so re-running at a different second changes those bytes. A fixed, committed sRGB profile would make outputs reproducible; ask the owner before changing it.
- Environment: Python 3, Pillow, defusedxml (`pip install -r skills/photo-framer/scripts/requirements.txt`). Tests take ~15 s.
- Put scratch outputs in the session scratchpad, not in the repo; `output/` is git-ignored but clean it up.
- When showing results to the owner, send contact sheets and state exactly what the input was.
- Commit messages end with the session's attribution lines; never put model names in commits or docs.
