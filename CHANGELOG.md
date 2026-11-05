# Changelog

Versions follow the rendering specification in `skills/photo-framer/references/presets.md`. The renderer reports its version with `python skills/photo-framer/scripts/frame_photo.py --version`. Three-digit choice codes are a frozen contract: no release changes the meaning of an existing code.

## v0.11.0 (2026-11-05): labels and signatures

- **Slots**: each style that can take overlays (A, B, E, G, H) exposes the margin below the photo as a slot. Text and images claim exact boxes there; anything that would leave the slot or overlap another item is rejected with a clear error. Nothing is ever drawn over the photo.
- **Gallery label for H**: `--title` in Inter SemiBold near-black and `--subtitle` in Inter Regular gray, the same faces and inks as D's camera line and exposure line, so one typeface runs through every style; centered below the photo. On fixed canvases the photo and label are centered together, so the photo moves up (as in the owner's 1:1 reference); on the thin border the canvas grows. The ink turns light on dark blurred backgrounds.
- **`--signature`** for A, B, E and G: the user's own PNG signature or logo, transparency kept, placed bottom-right (default), bottom-center or bottom-left in the margin below the photo, with `--signature-width` and `--signature-opacity`. H takes no signature (owner decision: a corner mark beside the centered label looks unbalanced).
- `--caption` stays separate (owner decision) and cannot be combined with the H gallery label. **One typeface across styles:** `--caption` no longer requires `--font`; by default it uses the bundled Inter Regular (C: Inter SemiBold, as its caption replaces the camera line). Commands that pass `--font` keep their font. **One text palette:** the caption gray on A, B, G and H is now sRGB (115,115,115), the gray of the exposure line and the H subtitle (was (100,100,100)); E keeps its contrasting inner-edge color and C its camera-line ink, so captioned A/B/G/H renders change slightly.
- `--preview` labels use Inter SemiBold instead of Pillow's default face. The preview now also shows H's gallery label and the `--signature` on A, B, E, G and H; a panel whose margin cannot hold the signature is labeled instead of failing the sheet.
- C no longer repeats the brand its logo or wordmark shows: a leading brand word is dropped from unlisted model names (`Canon EOS R5` → `EOS R5`, `NIKON D850` → `D850`); D keeps the full name. The JSON notes record the change.
- New README example: the Prague portrait on 1:1 with a gallery label.
- Without the new flags, every output is byte-identical to v0.10.

## v0.10.0 (2026-11-05): style H extensions

- `--ratio 4:5|1:1|3:4|9:16|original` for H. 3:4 and 9:16 are new (minimum margins 4.0% and 5.0% of the canvas width, share copies exactly 1080×1440 and 1080×1920); the menu codes keep their meaning.
- `--background blur` for H: the canvas is filled with a blurred copy of the photo itself (computed on a small copy, then enlarged), slightly darkened by default; `--blur-tone dark|neutral|light`. The photo stays intact on top, with its keyline.
- H output limit raised to 100 MP (other styles stay at 60 MP). Fixed a verification bug that rejected any output above 60 MP: Pillow's decompression-bomb limit (twice the 30 MP input cap) also applied when re-opening the file just written.
- `--preview` honours `--ratio` and `--background` for H, and labels it accordingly.
- New README examples: landscape and portrait on 9:16 with a blurred background.
- Without the new flags, every output is byte-identical to v0.9 (`tools/golden.py compare --base claude/phase2-metadata`).

## v0.9.0 (2026-11-05): metadata layer

- **Output EXIF is now kept by default** (deliberate behaviour change, approved by the owner). The final PNG and the share JPEG carry the source EXIF, including GPS location, with Orientation reset to 1, pixel dimensions updated, and the embedded thumbnail, maker notes and XMP (including edit history) dropped. `--metadata strip` restores the previous behaviour of writing no EXIF. Previews never carry metadata.
- **Camera display names** for C/D from `assets/cameras.json` (selected Sony α, Panasonic LUMIX and Nikon Z bodies): `ILCE-7C` shows as `α7C` in C beside the SONY mark and `Sony α7C` in D. Unlisted models are unchanged. `--raw-model` keeps the EXIF code; JSON notes record each rename.
- **Typed capture details** for C/D: `--camera`, `--lens`, `--iso`, `--aperture`, `--shutter`, `--focal` for film scans and files without EXIF. They override EXIF/XMP field by field, are shown as given, never select a brand mark, and are listed in the JSON notes.
- The C and D README examples were re-rendered with the display name.
- Checked with `tools/golden.py compare --new-flags "--metadata strip"` against v0.8: the only output changes are the C/D/preview renders of a camera now shown by its product name.

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
