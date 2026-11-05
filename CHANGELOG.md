# Changelog

Versions follow the rendering specification in `skills/photo-framer/references/presets.md`. The renderer reports its version with `python skills/photo-framer/scripts/frame_photo.py --version`. Three-digit choice codes are a frozen contract: no release changes the meaning of an existing code.

## v0.8.0 (2026-11-05): foundation refactor

No change to rendered output: every style, every choice code, text variants, captions, `--share` and `--preview` were checked byte-for-byte against v0.7 with `tools/golden.py` (Python 3.13 with Pillow 12.3, and Python 3.10 with Pillow 10.1).

- The renderer is now the `scripts/photoframer/` package. `scripts/frame_photo.py` remains the CLI entry point, so existing commands work unchanged.
- One module per style under `photoframer/styles/` declares its code, VI/EN names, menu rows, default code, accepted named flags and layout. An ordered registry drives the CLI, the preview and the docs.
- `render()` takes a `Settings` object (style, choice code, named options) instead of positional arguments.
- Named-flag compatibility matrix: each style lists the flags it accepts or requires; other flags are rejected with the same error messages as before. The matrix is published in the README and `references/menus.md`.
- `tools/gen_docs.py` generates the README style table, the VI/EN menu tables and the matrix; CI fails when they are stale.
- `SKILL.md` keeps routing and global rules; per-style agent rules moved verbatim to `references/styles/`.
- New `--version` flag.

## v0.7 (2026-11-05): style H, Minimal Mat

- H, default `1-1-1`: fixed 4:5 or 1:1 canvas, or a thin border following the photo's ratio; white, warm light gray or ivory mat; thin, no or thick black keyline. The photo is fitted and centered, never scaled or cropped.
- `--share` gives exactly 1080×1350 (4:5) or 1080×1080 (1:1).
- Portrait examples in the README.

## v0.6 (2026-10-27): style G, Deckled Paper

- Deterministic cotton-paper texture, torn outer edges and a soft contact shadow, all outside the rectangular photo.

## v0.5 (2026-10-27): style F, Film Edge

- Dark border with side sprockets and two independent corner texts (`--left-text`, `--right-text`, explicit blanks allowed).

## v0.4 (2026-10-27): style E, Color Echo

- One automatic, edge-weighted border color per photo, optional inner edge; `--frame-color` for one shared batch color.

## v0.3 (2026-10-26): style D, custom spec card

- C's layout with the user's exact `--right-text` in place of the brand mark.

## v0.2 (2026-10-26): style C, print/spec card

- Capture details from EXIF, then XMP, never invented; bundled brand marks or a text wordmark; bundled Inter fonts.

## v0.1 (2026-10-03): styles A and B

- A floating photo with a soft shadow, B gallery frame with white mat.
- Full-resolution PNG keeping photo pixels and ICC profile, optional sRGB share JPEG, `--preview` comparison, explicit `--crop`.
- Rejection of 16-bit PNG and unprofiled CMYK, transparency flattened on white, atomic no-overwrite saves, regression tests and CI.
