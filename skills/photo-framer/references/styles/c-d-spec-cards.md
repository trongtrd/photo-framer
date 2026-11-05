# Styles C/D: capture details, brand marks and custom text

Part of the [Photo Framer skill](../../SKILL.md); global rules there still apply. Menus: [menus.md](../menus.md); constants: [presets.md](../presets.md).

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

## Asking for D's text

For D, ask for the exact right-side text if it has not already been supplied:
"Bạn muốn điền chữ gì ở góc dưới bên phải?" / "What exact text would you like
at the bottom right?" It may be a location, photographer name, date, or a
combination. Preserve the user's wording, punctuation and Vietnamese accents.
Do not infer it from GPS, capture dates, filenames or context. An empty answer
does not authorize invented text; wait for the wording or a different style.
If D, its defaults and text are already explicit, run directly without asking again.
