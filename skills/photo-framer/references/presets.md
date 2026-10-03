# Rendering specification v0.1

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

Square corners. Shadows never cover photo pixels. RGB final files retain source ICC; decorative numeric colors are interpreted in that profile. Preview/share versions convert to sRGB. EXIF/GPS are excluded. Cropping/resizing requires explicit authorization; reduced previews are not final files.
