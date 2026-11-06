---
name: photo-framer
description: Add floating shadows, gallery frames, EXIF spec cards, custom text, Color Echo, Film Edge, Deckled Paper, or Minimal Mat (fixed 4:5 / 1:1 / 3:4 / 9:16 / 16:9 canvas, thin border, optional blurred background) frames to JPEG/PNG photographs with deterministic Python processing. Use for framing, matting, khung ảnh, ảnh nổi, bo giấy, viền phim, giấy xé, khung 4:5, khung vuông, khung ngang 16:9, viền trắng mỏng, camera details, or batch framing. Offer styles A/B/C/D/E/F/G/H while preserving photo content.
---

# Photo Framer

Use the bundled Python script. Do not regenerate or retouch photographs with AI. Keep original input files untouched.

## Inputs and runtime

1. Resolve only user-requested images using the host's supported file tools. Inspect images visually for border/crop handling and delivery. For E batches, inspect representative inputs/outputs instead of opening every image for color selection; Python handles each file's color and pixel checks.
2. Accept JPEG and 8-bit PNG; at most 30 encoded megapixels per input and **24 megapixels for the complete framed output in every style**. The usable source size depends on the layout; a wide photo on H 9:16 can produce more than three times as many pixels. The renderer checks layout before allocating a canvas and reports a suitable source size on rejection. Offer a smaller export or ask permission to resize a separate copy to that size before framing; never silently downsize or modify the original. File size in MB does not predict decoded RAM.
3. Locate `scripts/frame_photo.py` relative to this skill; it needs the `scripts/photoframer/` package beside it. Use Python 3.10+ and install dependencies from `scripts/requirements.txt`: Pillow 10.1–12.x and defusedxml for XMP reading. If missing, use the host's approved dependency installation procedure. No API key or network is needed by the renderer.
4. If code execution or image file access is unavailable, explain the missing capability. Do not claim support for every ChatGPT session or that a GitHub URL alone installs the skill.

## Existing borders

When an image appears already framed, or the user says it is, ask:
1. Keep the existing border and add a new frame outside it.
2. Remove the old border: propose a crop, display a crop preview, wait for approval.
3. Skip this image.

Never infer cropping authorization from a framing request. White areas may belong to the photograph. Border identification is visual and fallible. Use `--crop LEFT TOP RIGHT BOTTOM` only after approval, on one image at a time. Coordinates refer to the image after EXIF rotation. Create the crop preview using authorized local image-processing tools.

## Interaction

Use the user's language and [menus.md](references/menus.md). Preserve codes across languages.

Lead with the short display names when offering styles: Shadow / Ảnh nổi (A),
Gallery / Khung gallery (B), Specs / Thông số (C), Specs + Text / Thông số + chữ riêng (D),
Color / Viền màu (E), Film / Viền phim (F), Paper / Giấy xé (G), Canvas / Khung tỷ lệ (H).
Map these names, the previous names and letters to the same existing style codes;
pass letters to the CLI, which has no new name aliases. Use `Style · Variant`
for a named example, and show only the distinguishing appearance or text option
inside a style group. Keep the three-number codes available in the detailed menu.
Honor a request such as "Film, no text" as an explicit choice to leave both
corner fields blank; it does not authorize blank corners for other requests.

- A: floating photo, default **2-2-1**.
- B: gallery frame, default **1-2-1**.
- C: print/spec card, default **2-1-1** (medium margin, white, full caption).
- D: custom spec card, default **2-1-1** (same as C, user text replaces the logo).
- E: Color Echo, default **2-1-1** (medium border, muted auto color, thin inner edge).
- F: Film Edge, default **2-1-1** (medium border, charcoal, standard sprockets).
- G: Deckled Paper, default **2-1-1** (medium margin, warm-white paper, subtle torn edges).
- H: Minimal Mat, default **1-1-1** (fixed 4:5 portrait canvas, white, thin black keyline).
- Default style: A. If the user says only "use defaults" / "dùng mặc định", use A unless another style is already specified.

Honor supplied choices. For "A default", "B mặc định", or a full code such as "B, 1-3-1", skip style/settings questions and comparison. D still requires its right-side text; F requires an explicit choice for both corner fields, including intentional blanks.

Otherwise:
1. Generate an A/B/C/E/F/G/H comparison using `--preview` on the first uploaded photo; identify it as representative of the batch. F's preview corners stay blank until wording is supplied, and its label says text is chosen later. Add `--right-text` to include D. Add both `--left-text` and `--right-text` to preview F with supplied wording; empty fields are allowed and an empty right field omits D. Do not invent placeholder text or infer consent to final blank corners from a preview. When the user already supplied H's `--ratio`, `--background`, `--title`/`--subtitle` or a `--signature`, pass them to `--preview` too; panels whose margin cannot hold the signature are labeled instead of failing the sheet.
2. Display the comparison and offer A, B, C, D, E, F, G or H. Explain that D uses C's layout with user text instead of the logo, and that H's preview shows its 4:5 canvas while 1:1 and a thin border are also available. Use interactive choices when available, with codes in labels; otherwise use a short text menu.
3. Once style is chosen, show its three-row menu in one turn, marking defaults. Accept three-number answers, "default", or natural language mapped explicitly to presets.
4. If the choice UI returns no answer, apply the stated defaults instead of repeating questions. If the user explicitly wants to approve an appearance change, wait.
5. Apply choices across the batch, splitting runs for per-image exceptions.

## Style rules: read the style file before asking or running

Per-style behaviour lives in `references/styles/`. Open the file for the chosen style before asking its questions or running it; the one-line rules below are the minimum and always apply.

- C/D: [c-d-spec-cards.md](references/styles/c-d-spec-cards.md). Capture details come only from EXIF/XMP or values the user typed (`--camera`, `--lens`, `--iso`, `--aperture`, `--shutter`, `--focal`), never invented; the brand mark is pasted unmodified. D needs the user's exact `--right-text`: ask "Bạn muốn điền chữ gì ở góc dưới bên phải?" / "What exact text would you like at the bottom right?" and never infer it.
- A/B gallery labels: [a-b-gallery-labels.md](references/styles/a-b-gallery-labels.md). Use exact `--title`/`--subtitle`; grow the lower margin as needed, keeping the photo unchanged. Choose the label separately from captions and signatures.
- E: [e-color-echo.md](references/styles/e-color-echo.md). One automatic color per photo for the whole batch, no per-image questions or color variants; `--frame-color` once for a shared color.
- F: [f-film-edge.md](references/styles/f-film-edge.md). Both `--left-text` and `--right-text` are required, an empty value only when the user chose a blank corner; ask for missing fields together.
- G: [g-deckled-paper.md](references/styles/g-deckled-paper.md). Texture and torn edges stay outside the intact photo; no text by default.
- H: [h-minimal-mat.md](references/styles/h-minimal-mat.md). Fixed 4:5 / 1:1 canvas or thin border, plus `--ratio 3:4|9:16|16:9`, `--background blur` on every ratio, and a gallery label (`--title`/`--subtitle`); the photo is fitted and centered, never cropped or scaled. Square blur uses `--ratio 1:1 --background blur`; landscape blur uses `--ratio 16:9 --background blur`.
- Named flags and the styles that accept them: the matrix at the end of [menus.md](references/menus.md#named-options--tùy-chọn-có-tên). Choice codes never change meaning.

Do not silently substitute presets for explicit out-of-range pixel requests. Explain supported choices or make a scoped user-authorized renderer change.

## Execution

Quote paths safely. Resolve the actual skill path; never hardcode a machine-specific path.

```bash
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/photo.jpg" --preview --out-dir "/path/output"
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/landscape.jpg" "/path/portrait.jpg" \
  --style A --choices 2-2-1 --out-dir "/path/output"
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/photo.jpg" --style B --choices 1-3-1 \
  --share --out-dir "/path/output"
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/photo.jpg" --style C --out-dir "/path/output"
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/photo.jpg" --style D --right-text "Berlin, Germany | October 2022" \
  --out-dir "/path/output"
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/photo-1.jpg" "/path/photo-2.jpg" --style E --out-dir "/path/output"
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/photo-1.jpg" "/path/photo-2.jpg" --style E --frame-color "#ad896c" \
  --out-dir "/path/output"
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/photo.jpg" --style F --left-text "Berlin, Germany" \
  --right-text "October 2022" --out-dir "/path/output"
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/photo-1.jpg" "/path/photo-2.jpg" --style G --out-dir "/path/output"
python3 "$SKILL_DIR/scripts/frame_photo.py" \
  "/path/landscape.jpg" "/path/portrait.jpg" --style H --choices 1-1-1 \
  --share --out-dir "/path/output"
```

Final PNG adds the frame outside the full-resolution photo. `--share` additionally exports an sRGB JPEG with longest edge at most 2048 px. Label reduced JPEG comparisons as previews.

Keep RGB photo pixels and their ICC profile in final PNGs; normalize EXIF rotation first. Disclose conversion of supported profiled non-RGB images to sRGB. Reject unprofiled CMYK and high-bit-depth files. Transparent images are flattened on white paper: tell the user before processing when transparency matters, and never claim preservation of alpha or all original pixels. Final PNGs and share JPEGs keep the source EXIF by default, including GPS, with orientation reset and thumbnail/maker notes removed; this is the owner-approved default, so do not add warnings or questions about it. If the user asks to remove metadata or location, add `--metadata strip`. Previews carry no metadata.

The renderer checks PNG bit depth before decoding, including RGB and alpha PNGs. For grayscale images with an ICC profile, it preserves alpha/transparency-key information before converting color, then composites onto white paper.

Add a caption, gallery label or signature only when requested, using exact supplied wording. The A/B/G/H gallery label uses `--title` and optional `--subtitle` (bundled Inter, the same faces as D, no `--font` needed); never infer them from metadata, filenames or the photo. A/B/G grow their lower margin only as needed, keeping the photo's size and position; H centers the photo and label together on fixed canvases. A gallery label cannot be combined with `--caption` or `--signature`. `--signature` takes only a PNG the user supplies as their own signature or logo (A, B, E, G; not H, whose centered label would be unbalanced by a corner mark; `--signature-position`, `--signature-width`, `--signature-opacity`); never draw, generate or copy a signature yourself. If a label or signature does not fit or would overlap, ask for shorter wording, a smaller size or another position. D uses `--right-text`; F uses both `--left-text` and `--right-text`; these use the bundled fonts. For a separate caption on A–E, G or H, pass `--caption`; it uses the bundled Inter like every other text, so all styles share one typeface. Pass `--font` only when the user asks for another font, and then visually check Vietnamese glyphs. Keep text outside the photo. Never copy signatures from reference images. If text cannot fit, ask for shorter text or a suitable layout choice.

For per-image typed capture details in a C/D batch, use `--capture-sidecar` only when the user requests their JSON files. Each input reads its exact UTF-8 sibling `<complete input filename>.json` (for example `scan.jpg.json`), containing only the six capture fields above. Explicit capture flags win over JSON, which wins over EXIF/XMP field by field. Nothing is inferred or written back to EXIF. Missing siblings and malformed per-image files are reported separately; inspect every result. See the C/D reference for the schema and examples.

## Verification and delivery

Check every item in the JSON results. Report successes and errors separately; never infer batch success merely from process completion.

The script verifies file structure, fully decodes PNGs, and compares the photo region with the prepared source before exposing a final filename. Numeric suffixes prevent overwrites. Also inspect final images visually.

Save outputs through the host's authorized artifact mechanism when available. Provide previews and download links, distinguishing temporary files from persistent outputs if saving is blocked. Never publish photos to GitHub or elsewhere without authorization for that destination.

The skill has no remote image service, analytics, or automatic public upload. See [presets.md](references/presets.md) for constants and the approved default shadow.

When changing the renderer (`scripts/photoframer/`: one module per style under `styles/`, shared drawing in `components/`), run `python3 scripts/test_frame_photo.py` from this skill directory after installing `scripts/requirements.txt` (it runs every module in `scripts/tests/`; `-k NAME` filters, shared helpers are in `tests/support.py`). The CLI regression tests generate their own images and grayscale ICC profile; they use Pillow and defusedxml and do not use personal photos.
