---
name: photo-framer
description: Add floating-photo shadows, gallery frames, EXIF spec cards, or spec cards with custom right-side text to JPEG/PNG photographs using deterministic Python processing. Use for photo borders, framing, matting, khung ảnh, ảnh nổi, bóng đổ, bo giấy, or camera details with a location, photographer name or date. Offer styles A/B/C/D with explicit defaults while preserving photo content.
---

# Photo Framer

Use the bundled Python script. Do not regenerate or retouch photographs with AI. Keep original input files untouched.

## Inputs and runtime

1. Resolve only user-requested images using the host's supported file tools. Inspect them visually.
2. Accept JPEG and 8-bit PNG; at most 30 megapixels per input and 60 megapixels per output. Request a smaller copy or explicit resizing authorization if necessary; never quietly downsize final images.
3. Locate `scripts/frame_photo.py` relative to this skill. Use Python 3.10+ and Pillow 10.1–12.x. If missing, use the host's approved dependency installation procedure. No API key or network is needed by the renderer.
4. If code execution or image file access is unavailable, explain the missing capability. Do not claim support for every ChatGPT session or that a GitHub URL alone installs the skill.

## Existing borders

When an image appears already framed, or the user says it is, ask:
1. Keep the existing border and add a new frame outside it.
2. Remove the old border: propose a crop, display a crop preview, wait for approval.
3. Skip this image.

Never infer cropping authorization from a framing request. White areas may belong to the photograph. Border identification is visual and fallible. Use `--crop LEFT TOP RIGHT BOTTOM` only after approval, on one image at a time. Coordinates refer to the image after EXIF rotation. Create the crop preview using authorized local image-processing tools.

## Interaction

Use the user's language and [menus.md](references/menus.md). Preserve codes across languages.

- A: floating photo, default **2-2-1**.
- B: gallery frame, default **1-2-1**.
- C: print/spec card, default **2-1-1** (medium margin, white, full caption).
- D: custom spec card, default **2-1-1** (same as C, user text replaces the logo).
- Default style: A. If the user says only "use defaults" / "dùng mặc định", use A unless another style is already specified.

Honor supplied choices. For "A default", "B mặc định", or a full code such as "B, 1-3-1", skip style/settings questions and comparison. D still requires the user's exact right-side text if it has not been supplied.

Otherwise:
1. Generate an A/B/C comparison using `--preview` on the first uploaded photo; identify it as representative of the batch. When the user has supplied D's custom text, add `--right-text` to include D in a two-by-two A/B/C/D comparison. Do not invent placeholder text.
2. Display the comparison and offer A, B, C or D. Explain that D uses C's layout with user text instead of the logo. Use interactive choices when available, with codes in labels; otherwise use a short text menu.
3. Once style is chosen, show its three-row menu in one turn, marking defaults. Accept three-number answers, "default", or natural language mapped explicitly to presets.
4. If the choice UI returns no answer, apply the stated defaults instead of repeating questions. If the user explicitly wants to approve an appearance change, wait.
5. Apply choices across the batch, splitting runs for per-image exceptions.

For D, ask for the exact right-side text if it has not already been supplied:
"Bạn muốn điền chữ gì ở góc dưới bên phải?" / "What exact text would you like
at the bottom right?" It may be a location, photographer name, date, or a
combination. Preserve the user's wording, punctuation and Vietnamese accents.
Do not infer it from GPS, capture dates, filenames or context. An empty answer
does not authorize invented text; wait for the wording or a different style.
If D, its defaults and text are already explicit, run directly without asking again.

## Styles C/D: capture details, brand marks and custom text

C and D build the left-side details from the photo itself: EXIF first, then the XMP that
Lightroom writes into exports. Line 1 is `Model | LensModel`; line 2
(`ISO … f/… …s …mm`) appears only when every value exists. Never invent,
retype or estimate values. When a file carries no metadata, say so and offer
user-supplied `--caption` text or a text-free band (`C` with caption choice 3).
For D without metadata, keep the supplied right-side text and explain that
the left-side capture details are unavailable.

The brand mark is matched from Make/Model against `assets/logos/` (sources and
license terms in that folder's README) and pasted unmodified — no recoloring,
no distortion. Brands without a bundled logo (e.g. SIGMA, DJI) get a bold text
wordmark instead. The mark follows the camera body; a third-party lens does
not change it. Marks are stored next to this skill and need no network.

D never draws a brand mark or wordmark. Pass the exact wording with
`--right-text`. It uses the same font face, size, weight and color as the
camera/lens line on the left (bundled Inter SemiBold by default); a `--font`
override applies to both. D's third choice controls only the left-side details;
the right-side custom text remains visible in every mode. Keep it to one line,
up to 200 characters. If the text cannot fit alongside the details, ask for
shorter wording or fewer left-side details. Never shrink, truncate, rewrite
or wrap the supplied text to make it fit.

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
```

Final PNG adds the frame outside the full-resolution photo. `--share` additionally exports an sRGB JPEG with longest edge at most 2048 px. Label reduced JPEG comparisons as previews.

Keep RGB photo pixels and their ICC profile in final PNGs; normalize EXIF rotation first. Disclose conversion of supported profiled non-RGB images to sRGB. Reject unprofiled CMYK and high-bit-depth files. Transparent images are flattened on white paper: tell the user before processing when transparency matters, and never claim preservation of alpha or all original pixels. Original EXIF/GPS metadata is excluded from presentation files.

The renderer checks PNG bit depth before decoding, including RGB and alpha PNGs. For grayscale images with an ICC profile, it preserves alpha/transparency-key information before converting color, then composites onto white paper.

Add a caption/signature only when requested, using exact supplied wording. For D's right-side text, pass `--right-text`; it uses the bundled fonts. For a separate caption, pass `--caption` and `--font` with an available Unicode-capable font file. Visually check Vietnamese glyphs. Keep text outside the photo. Never copy signatures from reference images. If text cannot fit, ask for shorter text or a suitable layout choice.

## Verification and delivery

Check every item in the JSON results. Report successes and errors separately; never infer batch success merely from process completion.

The script verifies file structure, fully decodes PNGs, and compares the photo region with the prepared source before exposing a final filename. Numeric suffixes prevent overwrites. Also inspect final images visually.

Save outputs through the host's authorized artifact mechanism when available. Provide previews and download links, distinguishing temporary files from persistent outputs if saving is blocked. Never publish photos to GitHub or elsewhere without authorization for that destination.

The skill has no remote image service, analytics, or automatic public upload. See [presets.md](references/presets.md) for constants and the approved default shadow.

When changing image loading or color handling, run `python3 scripts/test_frame_photo.py` from this skill directory. The CLI regression tests generate their own images and grayscale ICC profile; they require only Python and Pillow and do not use personal photos.
