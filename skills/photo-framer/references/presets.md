# Rendering specification v0.1 (A, B) / v0.2 (C) / v0.3 (D) / v0.4 (E) / v0.5 (F) / v0.6 (G)

All geometry scales with the shorter oriented photo edge `s`.

## A: floating photo
- Margin: narrow 0.10s, medium 0.165s, wide 0.23s.
- Broad shadow: Gaussian radius 0.018s, offset (-0.014s,+0.014s), opacity 85/255.
- Contact shadow: Gaussian radius 0.006s, offset (-0.006s,+0.006s), opacity 41/255.
- Strength: light 0.60, medium 1.00, strong 1.40.
- Medium is the approved v2 default, approximately 25% higher layer opacity than the initial 68/255 and 33/255 prototype.
- Background: white #ffffff, ivory #faf8f3, light gray #f2f2f2.

## B: gallery
- Mat: narrow 0.10s, medium 0.16s, wide 0.23s.
- Frame 0.035s; wall margin 0.18s.
- Frame: black (32,32,31), white (242,242,240), charcoal (66,66,65).
- Top edge highlight: channels +10, capped at 255.
- Broad outer shadow: radius 0.032s, offset (0,0.018s), opacity 76/255.
- Contact outer shadow: radius 0.009s, offset (0,0.007s), opacity 48/255.
- Inner shadow: outside mask 105/255, radius 0.011s, cropped to mat opening.
- Wall: gray #5a5a5a, white #ffffff, ivory #faf8f3.

## C: print / spec card (added in v0.2)
Flat presentation: no shadow, frame or keyline.
- Side/top margin: narrow 0.022s, medium 0.035s, wide 0.055s (minimum 6 px).
- Bottom caption band: max(0.12s, 3.6 × caption font size, 44 px).
- Caption font 0.018s (minimum 9 px), typeset in bundled Inter
  (`assets/fonts/`, SIL OFL): SemiBold (30,30,30) for the gear line, Regular
  (115,115,115) for the exposure line. A user `--font` replaces both faces;
  without the bundled files Pillow's default face is used and a 0.028×font
  stroke imitates the heavier weight. Wordmark fallback (40,40,40), 1.6×font,
  emphasis face.
- Line 1 `Model | LensModel`; line 2 `ISO n  f/n  1/ns  nmm`.
- Glued "Mark" generations in EXIF model names are spaced for display only
  (`E-M10MarkIV` → `E-M10 Mark IV`); other compact names stay verbatim and
  each rewrite is disclosed in the JSON notes. The stored metadata never
  changes.
- Metadata read from EXIF first, then XMP (Lightroom exports keep XMP only);
  line 2 requires every value, otherwise it is skipped. Nothing is fabricated.
- Brand mark from `assets/logos/<slug>.png`, pasted unmodified (no recolor):
  height ≤ 2.8 × caption font and ≤ 66% of the band, width ≤ 34% of the photo.
  Brands without a bundled logo get a bold text wordmark. Marks persist when
  text is disabled; the wordmark does not.
- Background: white #ffffff, ivory #faf8f3, light gray #f2f2f2.
- Choices order: margin–background–caption; default 2-1-1 (medium, white, full).

## D: custom spec card (added in v0.3)
- Same geometry, colors and EXIF/XMP handling as C; no logo or wordmark.
- Required `--right-text`: verbatim user wording, one line, at most 200 characters.
- Right-aligned within the photo's right edge, vertically centered in the band.
- Exactly the gear line's font face, size, SemiBold weight, stroke and (30,30,30)
  color. A supplied `--font` replaces both faces consistently; no larger wordmark face.
- Reserve the custom text's measured width plus a gap of max(0.6 × side margin,
  2 × font size) before the left details. Reject text that does not fit; do not
  shrink, truncate, wrap or discard left-side details to make room.
- Choices: margin–background–left-side details, default 2-1-1. Choice 3 hides
  only the left details; the supplied right text remains visible.
- Missing metadata leaves the left side blank; custom wording is never derived
  from GPS, capture dates or other metadata.
- Default comparison includes A/B/C/E/F/G. With `--preview --right-text "..."`,
  include D using that supplied text; never invent a placeholder.

## E: Color Echo (added in v0.4)
- Flat, square-cornered colored border; no shadow, logo or automatic caption.
- Border width: narrow 0.045s, medium 0.08s, wide 0.12s, minimum 6 px.
- Inner edge: thin max(1, 0.004s), none, medium max(2, 0.008s), rounded to pixels.
  Photo offset is border width + inner edge on every side.
- Choices: width–auto color tone–inner edge, default 2-1-1 (medium, muted, thin).
- Auto selection uses one aspect-preserving BOX sample no larger than 96×96,
  converted to sRGB. Pixels within 20% of any edge receive 3× weight.
- Exclude saturation < 0.10 and HLS lightness outside 0.14–0.86. Group RGB
  channels in 24-value bins. Rank by weighted frequency, favoring midtones
  and moderate chroma; deterministic tuple tie-breaks select one color.
- Muted: HLS lightness +0.06 clamped to 0.36–0.68; saturation ×0.7 clamped
  to 0.18–0.48. Natural keeps the selected color. Light sets lightness 0.80
  and saturation min(0.35, original ×0.5).
- No eligible sample colors: use warm neutral sRGB #e8e4dc for any tone.
- `--frame-color` supplies one exact opaque sRGB hex/name for the whole batch,
  bypasses sample analysis, and overrides the auto-tone choice.
- Inner edge: sRGB #181c24 for border brightness ≥0.45, otherwise #f4f0e8;
  brightness uses weighted channels (0.2126, 0.7152, 0.0722).
- Both decorative colors are converted from sRGB into the source RGB ICC
  profile for the final PNG. The photo pixels and ICC bytes remain unchanged.
- Preview E resolves the original photo's auto color before resizing, so its
  color matches the final. Comparisons use three columns: six styles by default,
  or seven when D is included with supplied text.
- Batch processing creates one result per input, no candidate variants or AI
  color analysis. JSON notes record the chosen sRGB hex for reuse.

## F: Film Edge (added in v0.5)
- Flat dark border, two side columns of rounded sprockets, two custom texts
  below the photograph. No logo, film brand, auto frame number or photo effects.
- Side margin: narrow 0.055s, medium 0.075s, wide 0.10s, minimum 12 px.
- Top margin max(8, 0.04s). Lower band max(44, 0.09s, 3 × font size).
- Backgrounds (sRGB): charcoal (24,24,23), black (8,8,8), dark brown (39,32,28).
  Sprockets and text use warm white (245,239,221). Convert decorative colors
  into the source RGB profile; photo pixels and profile bytes remain intact.
- Sprocket width min(max(5, 0.018s), side−4), height min(photo height,
  max(6, 0.026s)). Pitch max(hole height+4, ratio × s), with ratios 0.07
  standard, 0.10 sparse, 0.05 dense. Round geometry to pixels; center each
  column within the photo's height and side margin. Never enter the photo
  or the lower text band.
- Font max(9, 0.018s), bundled Inter SemiBold, with the same fallback/stroke
  as the gear face in C/D. A supplied `--font` applies to both text fields.
- Required final fields `--left-text` and `--right-text`; explicit empty values
  mean intentionally blank corners. Each field: one line, at most 200 characters.
  No automatic casing, metadata lookup, line wrapping, shrinking or truncation.
- Align visible left/right text edges with the photo's left/right edges.
  Share one baseline, vertically center the combined ink height in the band.
  Reserve a 2 × font size gap when both fields are present. Reject overflow.
- Choices: border width–background–sprocket spacing, default 2-1-1.
- Preview may show F without text, labeled as awaiting wording; it does not
  authorize blank final corners. With both flags, use their exact values.
  An empty F right field omits D from the comparison, since D needs nonempty text.

## G: Deckled Paper (added in v0.6)
- Intact rectangular photo on subtly textured cotton-style paper, with an
  irregular torn outer silhouette and soft contact shadow. No automatic text,
  metadata, logo or effects within the photograph.
- Paper margin: narrow 0.055s, medium 0.085s, wide 0.12s, minimum 12 px.
- Outer background padding max(10, 0.025s); photo offset is padding + margin.
  Total canvas adds twice that offset to both photo dimensions.
- Paper tones (sRGB): warm white (250,248,242), bright white (253,253,251),
  ivory (246,239,220). Fixed light-gray background (224,223,218).
- Torn edge amplitude max(2, ratio × s), with ratios 0.003 subtle, 0.005 medium,
  0.008 rough. A local seeded generator (92753) varies four inward edge paths;
  each has at most 770 points and interpolated coarse knots plus fine jitter.
  Outer mask smoothing radius 0.6 px. The photo opening remains fully covered.
- Shadow: mask blur max(1, 0.0035s), opacity 52/255, offset
  (max(1, 0.001s), max(1, 0.003s)). Round geometry to pixels.
- Paper texture: fixed 256×256 tile, seed 72819, channel noise −3…+3 and
  450 subtle short fibers. Cache up to 12 tone/profile combinations. Tile only
  the four visible paper strips, then paste the original photo last; never
  loop over full-resolution photo pixels to generate texture.
- Convert the sRGB texture and background into the source RGB ICC profile;
  retain the photo's exact decoded RGB pixels and ICC bytes. Local random
  generators preserve global random state and give repeatable output.
- Choices: margin–paper tone–torn edges, default 2-1-1. One set of choices
  can process the entire batch without per-image questions or AI calls.
- Optional `--caption` requires the exact wording and a supplied `--font`.
  Keep it inside the lower paper strip, reserving clearance for the torn edge;
  reject overflow instead of touching the photo or clipping to the outer edge.

Square photo corners. Shadows never cover photo pixels. RGB final files retain source ICC; A–D decorative numeric colors are interpreted in that profile, while E/F/G convert their sRGB colors into it. Preview/share versions convert to sRGB. EXIF/GPS are excluded. Cropping/resizing requires explicit authorization; reduced previews are not final files.
