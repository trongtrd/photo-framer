# Spec-band fonts

Two static instances of **Inter** (by Rasmus Andersson / The Inter Project
Authors) used by style C to typeset the caption band: Regular for the exposure
line, SemiBold for the gear line. Inter is a screen-first typeface with full
Vietnamese coverage, which suits digital spec cards and keeps Vietnamese
diacritics correct.

Licensed under the [SIL Open Font License 1.1](OFL.txt), which permits
redistribution and bundling; keep this license file with the fonts. Fetched as
static instances from Google Fonts (`family=Inter`, weights 400 and 600).
Alternatives evaluated for the same role: IBM Plex Sans, Manrope.

If both files are removed, the renderer falls back to Pillow's bundled default
face and re-applies a thin stroke to imitate the weight hierarchy.
