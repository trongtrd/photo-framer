# Changelog

Versions follow the rendering specification in `skills/photo-framer/references/presets.md`. The renderer reports its version with `python skills/photo-framer/scripts/frame_photo.py --version`. Three-digit choice codes are a frozen contract: no release changes the meaning of an existing code.

## v0.13.0 (unreleased): landscape H and a complete README gallery

- **Landscape H:** `--ratio 16:9` adds a fixed horizontal canvas, with plain or blurred backgrounds, all three blur tones, keylines and gallery labels. Its minimum margin is 5% of the short edge (height), equivalent to 2.8125% of canvas width, mirroring 9:16. Share JPEGs are exactly 1920×1080. The full photo stays unscaled and uncropped; the shared 24 MP output cap still applies. Existing choice codes and ratios are unchanged.
- **Square blur is now visible in the examples.** `--ratio 1:1 --background blur` already worked; it is demonstrated alongside the new 16:9 blur and the existing ratios.
- **README gallery:** replace the single vertical list and detached H subsections with eight style groups. A–G each have two independent horizontal rows; H has three (ratios, blur, details). The 91 representative examples show every preset value by changing one setting from the default, plus named options, rather than all 27 combinations. Small thumbnails link to larger reduced previews.
- Gallery thumbnails sit on exact-black presentation squares so white frame edges remain visible against GitHub's page. Film Edge (F) uses exact-white squares instead, so its dark film borders remain visible. These surrounds are outside the intact reduced frame and appear only in lossless thumbnail PNGs; linked larger previews retain their actual frame backgrounds. Thumbnail presentation is cached separately from renderer outputs.
- **Names lead the README:** Shadow, Gallery, Specs, Specs + Text, Color, Film, Paper and Canvas, with `Style · Variant` descriptions. Letters remain secondary; existing names, CLI codes and three-number defaults remain in the technical reference. The skill maps short names to the same codes. The main gallery has 87 examples; four C/D metadata/input examples move to the technical section, E's shared color joins appearance, and H's plain/blur ratios share one order. All 91 recipes and generated images remain intact. The banner labels and workflow illustrations follow the same wording.
- `tools/gallery.py` renders and verifies the examples through the CLI, records recipes and hashes in a manifest, and supports a fast `--check` in CI. `tools/gen_docs.py` also generates the README gallery. Text hashes normalize line endings for Windows/Unix checkouts; full-resolution source files stay untouched.
- The owner approved their selected sample-3 PNG signature for the public README, at width 0.12. Signature examples appear only on A/B/E/G; H still has no signature. The supplied artwork is documented separately and is not bundled with the installed renderer.
- Tests cover landscape geometry/margins, square and landscape blur pixel preservation, exact share sizes, preview routing and size suggestions. Golden also covers the previously supported square blur to protect existing output.

## v0.12.0 (unreleased): bounded outputs, capture sidecars and more gallery labels

- **24 MP output cap for every style.** Owner-approved replacement for the former 60 MP cap (100 MP for H). The complete oriented/cropped layout, including labels and borders, is checked before allocating a canvas; JPEGs are checked before decoding. Oversized results report the proposed canvas dimensions and a proportionate smaller source size that fits the selected settings. No resizing is automatic: exporting a smaller copy, or explicitly authorizing preprocessing of a separate copy, remains the user's choice. Three-digit codes, accepted layouts below the cap, and share sizes are unchanged.
- **Per-image capture JSON for C/D.** Opt-in `--capture-sidecar` reads the exact UTF-8 sibling `<complete input filename>.json`. Allowed fields: camera, lens, ISO, aperture, shutter and focal length. Explicit flags override JSON; JSON overrides EXIF/XMP field by field. Missing files are reported, malformed files fail only their own image, and typed values affect display only, never source/output EXIF or logo selection. A runnable synthetic example is included.
- **Gallery labels on A/B/G.** `--title` and optional `--subtitle` reuse H's Inter faces, sizes and inks. Only the lower surround, mat/frame or paper grows as needed; the photo's size and position stay unchanged. Labels stay separate from ordinary captions and signatures to preserve balance. H still rejects signatures. Preview panels show labels where supported and mark combinations shown without a signature.
- The shared label component replaces H's duplicated drawing code. Golden comparison now also covers existing H labels on every ratio and a blurred background. Added tests cover sidecar precedence and batch isolation, label geometry and photo preservation, shared limits, pre-decode rejection, EXIF orientation and actionable smaller-size suggestions.
- Golden normalizes Windows temporary roots to their resolved paths, matching output filenames when the OS uses an 8.3 username alias; new ratio cases use filesystem-safe names without colons. Near-24 MP synthetic render/share measurements on Windows peaked at about 342–558 MB across A–H; the pixel cap is not a fixed RAM guarantee.
- Sony α7C is the owner's current body and is already mapped (`ILCE-7C`: C `α7C`, D `Sony α7C`); no unverified camera names were added.

## v0.11.1 (2026-11-05): reproducible outputs and maintenance

- **Reproducible bytes.** Previews, share copies and photos without a profile used to embed an sRGB profile that LittleCMS built at run time with the current second in its header, so the same command gave different bytes from one second to the next. The renderer now embeds the committed `assets/profiles/srgb.icc`: LittleCMS's built-in sRGB (description "sRGB built-in", copyright "No copyright, use freely") with its creation date fixed at 2026-11-05. The bytes are identical for LittleCMS 2.15 (Pillow 10.1) and 2.19 (Pillow 12.3) apart from that date; Windows builds also write `MSFT` where Linux and macOS write `APPL` in the header's primary-platform field, so the bundled file (`APPL`) also makes outputs identical across operating systems. A test checks the file against the installed LittleCMS, ignoring only those two fields. Pixels are unchanged: `tools/golden.py compare --base <v0.11.0 revision> --ignore-icc-dates` finds all 296 cases and every output file identical on Python 3.13/Pillow 12.3 and Python 3.12/Pillow 10.1.0.
- `tools/golden.py` now compares every byte by default; `--ignore-icc-dates` restores the old date-zeroing for comparisons with revisions before this one.
- CI also runs Python 3.13 (Ubuntu, Pillow 12.x).
- New tests (`tests/test_color_profile.py`): the bundled profile equals LittleCMS's sRGB apart from the date, the renderer embeds exactly those bytes, and outputs rendered a second apart are byte-identical.
- The regression tests moved from one 1,400-line file into `scripts/tests/`, split by area (input files and color, C/D, E/F/G, H, labels and signatures, metadata, registry) with shared helpers in `tests/support.py`. `scripts/test_frame_photo.py` stays the entry point, so CI and every documented command are unchanged. The same 60 tests run with identical bodies.
- `docs/HANDOFF.md` rewritten after the seven stacked PRs (#1 to #7) were merged into `main`.
- Apart from the embedded profile's creation date, every output is byte-identical to v0.11.0.

## v0.11.0 (2026-11-05): labels and signatures

- **Slots**: each style that can take overlays (A, B, E, G, H) exposes the margin below the photo as a slot. Text and images claim exact boxes there; anything that would leave the slot or overlap another item is rejected with a clear error. Nothing is ever drawn over the photo.
- **Gallery label for H**: `--title` in Inter SemiBold near-black and `--subtitle` in Inter Regular gray, the same faces and inks as D's camera line and exposure line, so one typeface runs through every style; centered below the photo. On fixed canvases the photo and label are centered together, so the photo moves up (as in the owner's 1:1 reference); on the thin border the canvas grows. The ink turns light on dark blurred backgrounds.
- **`--signature`** for A, B, E and G: the user's own PNG signature or logo, transparency kept, placed bottom-right (default), bottom-center or bottom-left in the margin below the photo, with `--signature-width` and `--signature-opacity`. H takes no signature (owner decision: a corner mark beside the centered label looks unbalanced).
- `--caption` stays separate (owner decision) and cannot be combined with the H gallery label. **One typeface across styles:** `--caption` no longer requires `--font`; by default it uses the bundled Inter Regular (C: Inter SemiBold, as its caption replaces the camera line). Commands that pass `--font` keep their font. **One text palette:** the caption gray on A, B, G and H is now sRGB (115,115,115), the gray of the exposure line and the H subtitle (was (100,100,100)); E keeps its contrasting inner-edge color and C its camera-line ink, so captioned A/B/G/H renders change slightly.
- `--preview` labels use Inter SemiBold instead of Pillow's default face. The preview now also shows H's gallery label and the `--signature` on A, B, E and G; a panel whose margin cannot hold the signature is labeled instead of failing the sheet.
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
