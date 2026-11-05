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

Because final PNGs keep every photo pixel, the canvas grows with the photo; a
very large landscape on 4:5 can exceed the 60-megapixel output limit and is
reported as an error. With `--share`, 4:5 and 1:1 export exactly 1080×1350 and
1080×1080 sRGB JPEGs; ratio 3 uses the usual 2048 px limit.
