# Handoff: Photo Framer

Last updated: 2026-11-05 (end of the upgrade session).
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
| Tests | `skills/photo-framer/scripts/test_frame_photo.py` (~61 tests, ~22 s) |
| Docs generator | `tools/gen_docs.py`; CI runs `--check` |
| Byte-identity check | `tools/golden.py compare --base <rev> [--new-flags "..."]` (~1.5 min, compares two code versions on one machine) |
| CI | `.github/workflows/test.yml` (Ubuntu Python 3.10 with Pillow 10.1, plus Python 3.12 on Ubuntu, Windows and macOS) |
| Fonts and licences | `skills/photo-framer/assets/fonts/README.md` (Inter only) |
| Camera display names | `skills/photo-framer/assets/cameras.json` |

## Current state: seven stacked PRs, all green, none merged

The PRs are stacked: each one's base is the previous PR's branch.

| PR | Branch | Content |
|---|---|---|
| [#1](https://github.com/trongtrd/photo-framer/pull/1) → `main` | `claude/happy-ptolemy-vpmy5z` | Style H, portrait demo, original roadmap |
| [#2](https://github.com/trongtrd/photo-framer/pull/2) | `claude/tender-lovelace-j9q91m` | v0.8: package refactor, registry, `Settings`, generated docs. Output byte-identical |
| [#3](https://github.com/trongtrd/photo-framer/pull/3) | `claude/phase2-metadata` | v0.9: EXIF kept by default, camera display names, typed capture details |
| [#4](https://github.com/trongtrd/photo-framer/pull/4) | `claude/phase3-minimal-mat` | v0.10: H `--ratio 3:4/9:16`, `--background blur`, 100 MP limit |
| [#5](https://github.com/trongtrd/photo-framer/pull/5) | `claude/phase4-labels` | v0.11: slots, H gallery label, PNG `--signature` (A/B/E/G) |
| [#6](https://github.com/trongtrd/photo-framer/pull/6) | `claude/unify-fonts` | Captions and preview labels in Inter; caption gray matched to the exposure line |
| [#7](https://github.com/trongtrd/photo-framer/pull/7) | `claude/polish-c-preview` | C drops a duplicate brand word; preview shows labels and signatures; `openai.yaml` |

**Merge procedure.** The owner merges #1 first, then each PR in order. After each merge, retarget the next PR's base to `main`. If the owner squashes or rebases, rebase the next branch onto `main`. Fix any CI failure or review comment on the PR that owns the code, then merge that branch upward into the later branches, as was done for the H-signature removal.

**Branch permissions.** The original session pushed only to the branches above, each created with the owner's approval. Ask before pushing anywhere else.

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

## Lessons from this session

- **Photo data.** Never crop, alter or invent owner photos or test data without saying so. Use `docs/images/demo-source-final.jpg` and `demo-portrait-source.jpg`; the owner authorised both for publication.
- **Test assets in previews.** Stand-in assets shown to the owner must be visibly neutral. A test signature PNG drawn in a serif font caused confusion.
- **Typography.** The owner checks visual consistency closely: fonts, colors and balance. Compare new text against the C/D spec band before proposing it.
- **Generated sRGB profile.** Outputs that embed it carry a LittleCMS timestamp, so reruns differ in bytes (pixels are identical). `golden.py` zeroes the timestamp before hashing.
- **Pillow bomb limit.** It also applies when re-opening our own outputs. `io._allow_pixels` raises it to exactly the encoded size.
- **Memory.** A 97 MP H render peaks at about 1.24 GB RSS.

## Open proposals (not started; owner has not prioritised)

1. Reproducible outputs: commit a fixed sRGB ICC profile. This changes bytes but not pixels.
2. Lower memory for large H outputs: verify the photo region in strips instead of decoding it whole.
3. Split the test file by area and refresh this handoff.
4. Per-image sidecar JSON for typed capture details in batches.
5. Expand `cameras.json` after the owner reviews the list in #3.
6. Possibly extend the gallery label to A/B/G through the matrix (ask first).
7. A README signature example, once the owner supplies their PNG.

The owner's last instruction was to finish review and merging of #1 → #7 before new features.
