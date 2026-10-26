# Rendering specification v0.1 (A, B) / v0.2 (C) / v0.3 (D)

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
- Default comparison remains A/B/C until text is supplied. With
  `--preview --right-text "..."`, render A/B/C/D in a two-by-two comparison,
  using that text.

Square corners. Shadows never cover photo pixels. RGB final files retain source ICC; decorative numeric colors are interpreted in that profile. Preview/share versions convert to sRGB. EXIF/GPS are excluded. Cropping/resizing requires explicit authorization; reduced previews are not final files.
