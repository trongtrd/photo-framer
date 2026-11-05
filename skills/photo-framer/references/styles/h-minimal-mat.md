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

## Gallery label

`--title` adds a centered line below the photo in Inter SemiBold, the face and
near-black ink of D's camera line; `--subtitle` adds a second, smaller line in
gray Inter Regular, like the exposure line (it needs a title). Ask for the exact
wording, for example a place and a date, and use it verbatim; never take it
from GPS, capture dates or filenames. On fixed canvases the photo and label
are centered as one block, so the photo moves up; on the thin border the
canvas grows. The label switches to light ink over a dark blurred background.
A title wider than the canvas margins is an error: ask for shorter wording.
The label replaces `--caption` for H; the two cannot be combined.

H takes no `--signature`: a corner mark beside the centered label looks
unbalanced. Offer A, B, E or G when the user wants a signature or logo.

## Size limits and sharing

Because final PNGs keep every photo pixel, the canvas grows with the photo. H
shares the **24 megapixel total output cap** with every other style (owner
decision, v0.12, replacing the former 100 MP H cap). A landscape on 9:16 can
more than triple the pixel count. Check the final layout before allocating
the canvas; oversized results report a suitable smaller source size. Offer a
smaller export or ask explicit permission to resize a separate copy first.
Never change the original or silently shrink the final photo. With `--share`, fixed ratios export exactly
1080×1350 (4:5), 1080×1080 (1:1), 1080×1440 (3:4) or 1080×1920 (9:16) sRGB
JPEGs; the thin border uses the usual 2048 px limit.
