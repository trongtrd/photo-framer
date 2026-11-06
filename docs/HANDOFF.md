# Handoff: Photo Framer

Last updated: 2026-11-06 (owner-only main history published; approved README naming implemented).
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
| Tests | `skills/photo-framer/scripts/test_frame_photo.py` runs every module in `scripts/tests/`. Areas include input/color, C/D, E/F/G, H, labels/signatures, metadata, registry, capture sidecars and output preflight. Shared helpers and the `FramerCase` base class are in `tests/support.py`. One module: `python -m unittest tests.test_metadata` from `scripts/`; filter by name with `-k` |
| Docs generator | `tools/gen_docs.py`; CI runs `--check` |
| README gallery | `tools/gallery.py` defines and renders 91 representative examples (87 in the style gallery, four technical examples); `docs/gallery.md` documents sources/recipes, `docs/images/gallery/manifest.json` records hashes. CI runs `python tools/gallery.py --check` |
| Byte-identity check | `tools/golden.py compare --base <rev> [--new-flags "..."]` (~1.5 min, compares two code versions on one machine; every byte is compared, add `--ignore-icc-dates` only for a `--base` older than v0.11.1) |
| CI | `.github/workflows/test.yml` (Ubuntu Python 3.10 with Pillow 10.1, plus Python 3.12 on Ubuntu, Windows and macOS, and Python 3.13 on Ubuntu) |
| Fonts and licences | `skills/photo-framer/assets/fonts/README.md` (Inter only) |
| Bundled sRGB profile | `skills/photo-framer/assets/profiles/README.md` (`srgb.icc`: LittleCMS's built-in sRGB with a fixed date; how to rebuild it) |
| Camera display names | `skills/photo-framer/assets/cameras.json` |

## Current state

The latest verified `main` is `43c8281`, the owner-approved metadata-only rewrite of `08a191c` (PR #11's merge). All 57 commit trees and their parent graph are preserved; 45 commit IDs changed, 26 Claude author/committer identities were replaced, 33 Claude co-author trailers were removed and 37 old signature headers were removed from rewritten objects. A verified all-ref backup and commit map are retained locally in `output/contributors-review-2026-11-06/`. GitHub's contributor API now reports only `trongtrd` with 57 commits. CI on the rewritten main passed (run ID 42143980539). The v0.11.1 tag remains exactly `2f64ad02db53c5aa5a1b3380cea051c6cd19b3b0`; its existing release and original history were not moved. Historical SHA references below describe the original PRs and checks. v0.12/v0.13 have no separate releases.

PR #11 merged unreleased v0.13.0 from `codex/h-landscape-readme-gallery`: H 16:9, square/landscape blur examples, and a README gallery organized by A–H. The owner requested representative variants covering the visible controls, allowing two or three rows per style; A–G have two rows, H three. Their explicit opening/merge authorization applied to PR #11 only: https://github.com/trongtrd/photo-framer/pull/11. It does not authorize another PR, a release or branch deletion.

The current branch `codex/readme-clarity-film-background` was rebased onto the rewritten main without changing its tree, then implements the approved naming/grouping plan and white presentation surround for Film (F). The other styles keep black surrounds. Squares remain 432×432 PNGs, with at least 16 px of padding around the intact reduced frame; linked larger previews keep the actual frame background. All 91 generated examples remain unchanged apart from F's previously approved thumbnail surrounds. GitHub's table chrome follows the viewer's theme because custom README CSS is sanitized. Renderer behavior is unchanged. No PR or merge has been requested for this branch.

The owner explicitly approved all proposals on 2026-11-06, including the separately reviewed non-fast-forward update of main. `docs/proposals/readme-names.md` records the accepted display vocabulary: Shadow, Gallery, Specs, Specs + Text, Color, Film, Paper and Canvas. README headings put letters second, descriptive variants lead, and CLI flags/three-number codes remain in the technical reference. Four C/D metadata/input examples move there, E's shared color moves to appearance, and H uses the same ratio order in its plain/blur rows. The skill maps new and previous display names to the unchanged A–H codes. The history-update exception is complete; it does not authorize unrelated future force-pushes, changes to release tags or merges of new PRs.

Takeover verified `main` at `2f64ad0`, all nine PRs merged, 64 tests passing and CI run 55 successful in all five jobs. The local checkout was stale at `6408659` and was fast-forwarded without edits. The current workstation is Windows, Python 3.14.8/Pillow 12.3.0, rather than the previous session's Linux environment.

The owner approved publishing v0.11.1 and deleting the final merged branch. The GitHub Release and tag now point exactly at `2f64ad02db53c5aa5a1b3380cea051c6cd19b3b0`; `claude/lucid-shannon-h9z9t5` was deleted using the normal GitHub API. The old session's branch-deletion proxy restriction does not apply to this workstation. Automatic branch deletion was not enabled.

The owner approved capture sidecars and gallery labels on A/B/G, then explicitly approved a 24 MP total output cap with no silent resizing. This work was developed on `codex/capture-sidecars-gallery-labels` as unreleased v0.12.0. On 2026-11-06 the owner explicitly requested opening and merging the PR for this branch once checks pass. That authorization applies only to this change, not future PRs, a v0.12.0 GitHub Release, or publication of the private signature files. Verify the resulting PR's merge status and the latest `main` checks on GitHub.

Local v0.13 validation: 76 tests passed on Windows/Python 3.14.8/Pillow 12.3.0 (about 81 seconds initially, 75 seconds after the thumbnail update). Generated docs and all 91 gallery recipes/assets pass their checks. Golden against `5f49b92` passed 303 cases / 1,047 output files byte for byte, including previously supported square blur. New 16:9 behavior has separate geometry, pixel, share-size, preview and limit tests. All five branch CI jobs passed at `eeef0b9` (run 65). Native GitHub rendering was verified: all 93 black-surround thumbnails load at the intended size and wide rows scroll horizontally; the 91 larger previews remain unchanged. Check the final PR head and post-merge `main` CI before reporting integration complete.

Working rules for the next session:

- Use the branch the session names; push only there, and ask before pushing anywhere else. Do not open a PR unless the owner asks.
- Use the owner's configured Git identity and do not add AI co-author trailers; the owner requested that only their identity appear in Contributors.
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
  - `--caption` stays separate from the gallery label (`--title` / `--subtitle`), now available on A/B/G/H; the two cannot be combined. A/B/G keep the photo's size/position and grow only the lower margin as needed. H keeps its existing label layout.
  - Only exact user wording, never inferred.
- **Signatures**
  - `--signature` is a user-supplied PNG only. No text-signature option and no font are involved.
  - Allowed on A, B, E and G. **H has no signature**: a corner mark beside the centered label looked unbalanced.
  - Never generate a signature or take one from a reference photo. Use only a supplied PNG. The owner approved selected sample 3 for public README examples on 2026-11-06; the asset is `docs/images/gallery/signature.png`, placed at width 0.12. That artwork is not part of the installed renderer and is never automatically added to users' photos.
  - Gallery labels and signatures are separate choices on A/B/G to avoid the same centered-label/corner-mark imbalance.
- **H parameters**: 3:4 margin 4.0% of width, 9:16 margin 5.0% of width; shares 1080×1440 and 1080×1920. New 16:9 uses 5.0% of height (2.8125% of width), share 1920×1080. Blur works with every ratio, including 1:1, and darkens about 12% by default. The original three menu choices keep their meanings.
- **Output size (owner approved 2026-11-06):** every style is capped at 24 MP for the complete framed canvas, replacing H's 100 MP and the other styles' 60 MP limits. Check dimensions before allocating the canvas; report a suitable smaller source size when rejected. Ask before resizing a separate copy; never silently downsize or modify the original. Compressed MB is not a RAM budget.
- **Capture sidecars:** opt-in `--capture-sidecar` on C/D reads only the exact sibling `<input filename>.json` (UTF-8, at most 16 KiB, six capture fields). Explicit flags > JSON > EXIF > XMP. Display only; never invent fields, alter EXIF or select a logo from typed camera text. Missing siblings produce notes; malformed siblings fail only their own image.
- **Process**
  - Refactors must pass `golden.py`.
  - Every change updates CHANGELOG, docs and demo images in the same PR.
  - Do not open a PR unless the owner asks.

## Lessons

- **Photo data.** Never crop, alter or invent owner photos or test data without saying so. Use `docs/images/demo-source-final.jpg` and `demo-portrait-source.jpg`; the owner authorised both for publication.
- **Test assets in previews.** Stand-in assets shown to the owner must be visibly neutral. A test signature PNG drawn in a serif font caused confusion.
- **Typography.** The owner checks visual consistency closely: fonts, colors and balance. Compare new text against the C/D spec band before proposing it.
- **sRGB profile.** Since v0.11.1 the embedded sRGB is the committed `assets/profiles/srgb.icc`, so outputs are reproducible and `golden.py` compares every byte. LittleCMS 2.15 and 2.19 build the same bytes apart from the date and, on Windows, the primary-platform field (`MSFT` instead of `APPL`); a new LittleCMS could change the built-in profile, and `test_color_profile` (which ignores only those two fields) will say so. Lesson: a claim about bytes needs checking on Windows too, not only on the two Linux builds.
- **Pillow bomb limit.** It also applies when re-opening our own outputs. `io._allow_pixels` raises it to exactly the encoded size.
- **Memory.** A historical 97 MP H render peaked at about 1.24 GB RSS; v0.12 rejects such layouts. Windows measurements on Python 3.14.8/Pillow 12.3.0, using separate processes and synthetic JPEG inputs with near-24 MP outputs plus share copies: peak working set A 471 MB, B 375 MB, C 557 MB, D 558 MB, E 534 MB, F 549 MB, G 514 MB, H 9:16 blur 342 MB. These are example measurements, not a worst-case bound. Do not claim that the pixel cap is an absolute RAM guarantee.
- **Golden on Windows.** Resolve temporary roots before normalizing output paths: Windows may supply an 8.3 username alias, while saved filenames resolve to the long path. Golden case directory names must not contain ratio colons; use `9x16`, not `9:16`. Both issues were found and fixed during v0.12 validation; output file bytes had not changed.
- **Moving tests.** When tests are reorganised, check that the set of test names and their bodies are unchanged (the 2026-11-05 split was verified by comparing the AST of every test method before and after) and mutate one rendering constant to confirm the suite still fails.

## Open proposals and owner choices

1. Signature selection and publication are resolved: **sample 3**, width **0.12**, bottom-right, opacity 1.0. The owner approved public README use on 2026-11-06. The original three sources and comparison files remain in their Dropbox; only the selected transparent PNG is used by the documentation gallery. Background extraction/cropping used explicitly approved Python/Pillow processing; white recompositing exactly reproduces the cropped source pixels.
2. Camera names: the owner uses Sony α7C, already supported correctly; no expansion is needed for their current body. Other names remain subject to manufacturer verification before addition.
3. Capture sidecars, A/B/G labels and the 24 MP cap are complete through PR #10; landscape H and the gallery are complete through PR #11. Owner-only main attribution is published and verified. F's white surround and the approved naming/grouping changes are on `codex/readme-clarity-film-background`, pending a future PR request. Future PRs still require their own request and specific merge approval.

No other new feature or release is authorized. Commits, PR text and repository docs stay in English; conversation stays in Vietnamese.
