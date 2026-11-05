# Style F: Film Edge with two custom text fields

Part of the [Photo Framer skill](../../SKILL.md); global rules there still apply. Menus: [menus.md](../menus.md); constants: [presets.md](../presets.md).

F adds a flat dark border, rounded sprocket marks along the left and right
edges, and two independent text fields in the lower band. All decoration
stays outside the photo. No film brand, frame number, logo, metadata, grain,
scratches or color grading is added automatically.

If a corner's wording or blank choice is missing, ask once for the missing
fields together: "Bạn muốn ghi gì ở góc dưới trái và góc dưới phải? Có thể để
trống từng bên." / "What would you like at the bottom left and bottom right?
Either corner may be left blank." Keep already supplied fields. No reply
does not mean an intentional blank. Do not infer either field from metadata,
filenames or the example's text. Preserve spelling, case and punctuation.

Use `--left-text` and `--right-text`. Both flags are required for final F,
including blanks: use `--left-text=` or `--right-text=` for an intentionally
blank corner. The two fields share bundled Inter SemiBold, font size and
warm-white color; `--font` overrides both. Each is one line, at most 200
characters. If they cannot fit together, ask for shorter wording; do not
shrink, truncate, wrap or overlap the texts. Do not use `--caption` for F.

If the pair and settings are already supplied, run directly. Reuse an agreed
pair across a batch without repeated questions; split runs for requested
per-image differences. Never automatically fill a corner with `01`, `BERLIN`
or another string from a mockup.
