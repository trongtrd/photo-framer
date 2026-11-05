# Style H: Minimal Mat (fixed canvas or thin border)

Part of the [Photo Framer skill](../../SKILL.md); global rules there still apply. Menus: [menus.md](../menus.md); constants: [presets.md](../presets.md).

H places the intact photograph on a plain mat. Row 1 chooses the canvas:
1 = fixed **4:5 portrait** (the tallest ratio Instagram/Facebook feeds show
uncropped, best on phone screens), 2 = fixed **1:1 square**, 3 = a thin even
border that follows the photo's own ratio. With 4:5 and 1:1, landscape and
portrait photos share the same canvas: the photo is fitted (letterboxed, never
cropped or scaled) and centered both ways, keeping a minimum margin of 3.6%
(4:5) or 2.4% (1:1) of the canvas width on the binding side. Ratio 3 uses a
uniform border of 1.5% of the photo's short edge.

Row 2 is the mat: white, warm light gray (`#EBE5E5`) or ivory. Row 3 is the
black keyline drawn just outside the photo edge: thin (default), none or thick.
No text is added by default. Run a batch with one setting; previews are not
required for an explicit "H default".

## More ratios and a blurred background (named flags)

`--ratio 4:5|1:1|3:4|9:16|original` overrides row 1; the menu codes keep their
meaning, so 3:4 and 9:16 are reachable only through the flag. Map requests such
as "story", "reels", "9:16" or "phone wallpaper" to `--ratio 9:16`, and "3:4" to
`--ratio 3:4`. Minimum margins are 4.0% (3:4) and 5.0% (9:16) of the canvas width.

`--background blur` fills the canvas with the same photo, scaled to cover and
softly blurred, instead of the mat color (row 2 is then unused). The tone is
slightly darkened by default so the photo stands out; `--blur-tone neutral` or
`light` changes it. The blur lies only outside the photo; the photo is pasted
last, unchanged, and the keyline still applies. Offer it when the user asks
for a blurred, "frosted" or photo-colored background; do not switch it on
unasked.

## Size limits and sharing

Because final PNGs keep every photo pixel, the canvas grows with the photo. H
allows outputs up to 100 megapixels (other styles: 60), enough for a 29 MP
landscape on 9:16; the largest outputs need about 1.3 GB of memory. Larger
results are reported as errors. With `--share`, fixed ratios export exactly
1080×1350 (4:5), 1080×1080 (1:1), 1080×1440 (3:4) or 1080×1920 (9:16) sRGB
JPEGs; the thin border uses the usual 2048 px limit.
