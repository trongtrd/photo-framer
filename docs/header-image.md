# README header illustration

Asset: [`images/photo-framer-header.png`](images/photo-framer-header.png).

Generated with the built-in imagegen tool for the Photo Framer README. The visual direction follows the warm paper, navy typography and coral accents of the [Linear Writing header](https://github.com/trongtrd/linear-writing).

The banner is an editorial illustration of the three framing styles. The real photo examples in the README are separate outputs from the bundled Python renderer; the source photograph and those examples were not edited to make this banner.

The README displays the header at full width and links it to the examples section. Keep text alternatives and the written introduction available outside the image.

## Getting-started diagram

The README also uses [`images/photo-framer-workflow.svg`](images/photo-framer-workflow.svg)
and a [vertical mobile version](images/photo-framer-workflow-mobile.svg). These
editable SVGs share the header's paper, navy and coral colors. They show the user
journey: install the skill, attach photos, choose A–G, save the framed PNG.
The `<picture>` element selects the vertical diagram at viewport widths up to
600 px. No JavaScript, remote font or external image service is needed.

The diagram is a reading aid. Keep installation instructions, example requests
and output descriptions available as ordinary README text. Do not replace the
real photograph or its A–G examples when revising the diagram.

## Generation prompt

```text
Create one finished editorial header illustration for the GitHub README of PHOTO FRAMER, an English/Vietnamese AI-assistant skill that adds frames outside photographs. This is an original graphic banner, not a screenshot and not a photograph.

OUTPUT AND ART DIRECTION:
A wide 2:1 landscape banner, approximately 1800 by 900 pixels. Warm ivory paper background (#FAF7F0), deep midnight navy typography and line work (#112447), a restrained coral accent (#F66B58), small warm-gray secondary details. Flat editorial vector-like illustration, clean print-design finish, no interface chrome. Carefully typeset, extremely legible at a GitHub README width of about 830px. Generous negative space. Crisp orderly composition, not busy. Use the feeling of an intelligent editorial open-source project cover.

COMPOSITION:
Left 42%: huge, bold, condensed sans-serif product title stacked on two lines, EXACTLY:
"PHOTO"
"FRAMER"
A short coral horizontal rule below. Under the rule, a smaller but clearly readable navy subtitle on two lines, EXACTLY:
"Frame your photos."
"Keep the original."

Right 52%: an elegant schematic showing three ways of presenting the same simple abstract image. Use a single shared abstract picture motif: three tall warm-gray architectural columns with a small coral sun-like circle behind them. This must be geometric artwork, not a generated photo or a recreation of a real person's photograph. Repeat the SAME picture motif in all three frames. Arrange the three distinct photo cards in a deliberate compact editorial composition: the floating card above left, the gallery card above right, and a slightly larger spec-card centered underneath, without overlapping any picture or caption. Small coral A, B, C markers connect each readable label to its example.
A: a white paper surround with a modest soft shadow outside the picture; label EXACTLY "A / Floating".
B: a thin rigid navy-black outer frame, white mat, warm-gray wall area; label EXACTLY "B / Gallery".
C: a flat white narrow border and a taller lower caption band with two short fine gray rules indicating automatic metadata; label EXACTLY "C / Spec card". No shadow on C. The rules are schematic strokes, not fake camera text. No device logos, exposure numbers or fabricated metadata.

CONSTRAINTS:
Include only the title, subtitle, and three exact labels specified above. Do not add a slogan, badges, signatures, watermark, paragraph, controls, file formats, program code, photographic landscape, brand logo, or camera hardware. Keep all frame examples and labels comfortably inside the canvas with generous margins. The frame artwork should communicate floating / gallery / spec-card differences immediately. Professional, understated, visually compelling. The graphic is the finished cover itself; no mockup around it.
```
