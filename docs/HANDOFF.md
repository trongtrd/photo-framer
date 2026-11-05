# Handoff: Photo Framer

Last updated: 2026-11-05 (after the seven stacked PRs were merged).
Owner: trongtrd. Writes in Vietnamese: reply in Vietnamese, using photography and post-processing terms. Ask with `AskUserQuestion` and give a recommended option when a decision is really the owner's. Otherwise proceed.

## Where to read first (do not duplicate here)

| Topic | Source |
|---|---|
| Product, styles A–H, CLI examples, limits, demo reproduction, maintenance commands | `README.md` |
| Release history v0.1 → v0.11 (what each change did and why) | `CHANGELOG.md` |
| Agent rules (exact wording only, crop only with approval, verification) | `skills/photo-framer/SKILL.md`, per-style `skills/photo-framer/references/styles/*.md` |
| Menus (VI/EN), named-flag matrix | `skills/photo-framer/references/menus.md` (tables generated) |
| Geometry, colors, fonts, slots, EXIF rules | `skills/photo-framer/references/presets.md` |
| Renderer | `skills/photo-framer/scripts/photoframer/`: `styles/` (one module per style), `components/`, `registry.py`, `settings.py` (`Settings` and the `OPTIONS` matrix), `cli.py`. Entry point: `scripts/frame_photo.py` |
| Tests | `skills/photo-framer/scripts/test_frame_photo.py` runs every module in `scripts/tests/` (60 tests, ~30 s). Modules by area: `test_cli_and_input`, `test_spec_cards` (C, D), `test_styles_efg`, `test_style_h`, `test_labels_overlays`, `test_metadata`, `test_registry`; shared helpers and the `FramerCase` base class in `tests/support.py`. One module: `python -m unittest tests.test_metadata` from `scripts/`; filter by name with `-k` |
| Docs generator | `tools/gen_docs.py`; CI runs `--check` |
| Byte-identity check | `tools/golden.py compare --base <rev> [--new-flags "..."]` (~1.5 min, compares two code versions on one machine) |
| CI | `.github/workflows/test.yml` (Ubuntu Python 3.10 with Pillow 10.1, plus Python 3.12 on Ubuntu, Windows and macOS) |
| Fonts and licences | `skills/photo-framer/assets/fonts/README.md` (Inter only) |
| Camera display names | `skills/photo-framer/assets/cameras.json` |

## Current state

Everything through v0.11.0 is on `main`. The seven stacked PRs (#1 to #7: style H, the foundation refactor, the metadata layer, H ratios and blur, labels and signatures, one typeface, C and preview polish) were merged in order on 2026-11-05 with merge commits, each retargeted to `main` after the one below it. No stacked PRs remain. The old `claude/*` branches of that stack are fully merged and carry nothing that `main` lacks.

Working rules for the next session:

- Use the branch the session names; push only there, and ask before pushing anywhere else. Do not open a PR unless the owner asks.
- Before reporting a state, check it: run the tests and `python tools/gen_docs.py --check`, and read GitHub's check runs (the legacy status endpoint reports `pending` with no entries because CI uses check runs).
- Keep the CHANGELOG, docs and demo images in the same PR as the code change.

## Binding decisions (all phases)

- **Styles and codes**
  - Keep styles A–H. Add a new style only for genuinely new layout geometry.
  - Three-digit codes are frozen. New features arrive as named flags declared in `settings.OPTIONS` and each style's `accepts`/`requires`.
- **Metadata**
  - EXIF, including GPS, is kept by default (`--metadata strip` removes it). Never add warnings or extra questions about GPS.
  - Camera display names: C shows the short form beside the logo (`α7C`), D the full form (`Sony α7C`). Only add names confirmed against the maker's own naming.
- **Text and typography**
  - One typeface everywhere: bundled Inter only. Primary ink is (30,30,30); secondary ink is (115,115,115) (`text.PRIMARY_INK` / `SECONDARY_INK`). Never re-add a serif.
  - `--caption` stays separate from the H gallery label (`--title` / `--subtitle`); the two cannot be combined.
  - Only exact user wording, never inferred.
- **Signatures**
  - `--signature` is a user-supplied PNG only. No text-signature option and no font are involved.
  - Allowed on A, B, E and G. **H has no signature**: a corner mark beside the centered label looked unbalanced.
  - Never create or copy a signature. The README has no signature example until the owner supplies a PNG.
- **H parameters**: 3:4 margin 4.0%, 9:16 margin 5.0%. Share copies 1080×1440 and 1080×1920. Blur darkens about 12% by default. H outputs may reach 100 MP; other styles 60 MP.
- **Process**
  - Refactors must pass `golden.py`.
  - Every change updates CHANGELOG, docs and demo images in the same PR.
  - Do not open a PR unless the owner asks.

## Lessons

- **Photo data.** Never crop, alter or invent owner photos or test data without saying so. Use `docs/images/demo-source-final.jpg` and `demo-portrait-source.jpg`; the owner authorised both for publication.
- **Test assets in previews.** Stand-in assets shown to the owner must be visibly neutral. A test signature PNG drawn in a serif font caused confusion.
- **Typography.** The owner checks visual consistency closely: fonts, colors and balance. Compare new text against the C/D spec band before proposing it.
- **Generated sRGB profile.** Outputs that embed it carry a LittleCMS timestamp, so reruns differ in bytes (pixels are identical). `golden.py` zeroes the timestamp before hashing.
- **Pillow bomb limit.** It also applies when re-opening our own outputs. `io._allow_pixels` raises it to exactly the encoded size.
- **Memory.** A 97 MP H render peaks at about 1.24 GB RSS.
- **Moving tests.** When tests are reorganised, check that the set of test names and their bodies are unchanged (the 2026-11-05 split was verified by comparing the AST of every test method before and after) and mutate one rendering constant to confirm the suite still fails.

## Open proposals (not started; owner has not prioritised)

1. Reproducible outputs: commit a fixed sRGB ICC profile. This changes bytes but not pixels, so it needs the owner's approval; it would also remove the timestamp workaround in `golden.py`.
2. Lower memory for large H outputs: verify the photo region in strips instead of decoding it whole. Worth doing only if near-100 MP renders are real use.
3. Expand `cameras.json` after the owner reviews the list added in v0.9 (many names were written from memory).
4. A README signature example, once the owner supplies their PNG.
5. Per-image sidecar JSON for typed capture details in batches (new feature, ask first).
6. Possibly extend the gallery label to A/B/G through the matrix (ask first; weigh the balance argument that removed the H signature).

Done since the last handoff: the test file was split by area (this PR), and #1 to #7 were merged.
