# Style E: efficient Color Echo batches

Part of the [Photo Framer skill](../../SKILL.md); global rules there still apply. Menus: [menus.md](../menus.md); constants: [presets.md](../presets.md).

E adds a flat border with one color per photo, plus an optional contrasting
inner edge. By default, use auto color: the renderer analyzes a sample no
larger than 96×96 in sRGB, weights edge colors, favors midtones, and softens
the chosen color. Near-neutral, black/white or unusable samples fall back to
warm neutral `#e8e4dc`. The photograph itself is never recolored or resized.

For an explicit E request, run the whole batch with defaults unless different
settings were supplied. Do not generate three color options, call AI vision
for each color, or ask per-image color questions. Previews are optional and
only generated when requested. Capture the CLI JSON, check every result, and
summarize counts and errors rather than repeating every file's color notes.

For one shared color, pass `--frame-color "#ad896c"` (or a supported English
color name) once for the entire batch. This bypasses auto analysis and uses
that exact sRGB color, independent of the auto-tone setting. If the user asks
for a shared color without specifying one, ask once for the color or a
reference photo; resolve the reference color locally, then reuse its hex.
Do not choose a new shared color for each input. Split runs for explicit
per-image overrides. JSON notes include the selected sRGB hex for reuse.
