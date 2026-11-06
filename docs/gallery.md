# README gallery

The README leads with eight short display names: Shadow (A), Gallery (B),
Specs (C), Specs + Text (D), Color (E), Film (F), Paper (G), and Canvas (H).
Their agreed naming hierarchy is in `docs/proposals/readme-names.md`.
The main gallery has 87 examples. A–G use appearance and text rows; E's shared
color belongs with appearance. Each preset example changes one setting from
the default, so every menu value is visible without listing all combinations.
H uses three rows: ratios, blur and details, with the same ratio order in its
first two rows. C/D's four metadata/input examples are in the technical section.
All 91 examples remain generated and verified.

Names and descriptive variants lead the gallery. Letters remain secondary in
the group headings; CLI flags, legacy names and default three-number codes
are in the technical reference. This changes documentation and skill vocabulary,
not the renderer's codes, names or output bytes.

The number of columns is independent for every row. Wide tables can scroll
horizontally on GitHub; each thumbnail links to a larger JPEG. The README
uses HTML tables and image links rather than custom CSS. GitHub shrinks image
and cell width attributes to fit its container, so an accessibility-hidden
nonbreaking spacer supplies an intrinsic minimum width in each image cell.
This keeps the previews readable and activates native horizontal table scrolling.

Thumbnails are centered on opaque presentation squares: white (`#ffffff`)
for Film (F), black (`#000000`) for the other styles and the original
photos. White keeps F's dark film borders visible; black separates the light
mats from GitHub's page. These surrounds are not part of the rendered frame:
clicking a thumbnail opens the larger image without the presentation surround.
The table chrome still follows the viewer's GitHub theme; GitHub
sanitizes custom CSS in README files.

## Rebuild

Install the renderer requirements, then run from the repository root:

```sh
python tools/gallery.py
python tools/gen_docs.py
python tools/gallery.py --check
python tools/gen_docs.py --check
```

`tools/gallery.py` is the single example list. It renders through the public
CLI, checking every per-image result. The renderer verifies photo-region
pixels in the full-resolution PNG before the tool creates reduced JPEGs.
Intermediate files are confined to `output/gallery-renders` and removed
after verification; original photographs are never rewritten.

Larger gallery JPEGs have a longest edge of at most 1280 px. Thumbnail PNGs
are 432×432 px, with the intact frame reduced to at most 400 px and centered
with at least 16 px of white or black padding on every side. PNG keeps that
padding exactly white or black. They use the committed sRGB profile and contain no EXIF.
They are documentation previews, not full-resolution or exact-size share files.
The H renderer's actual share outputs remain 1080×1350 (4:5), 1080×1080 (1:1),
1080×1440 (3:4), 1080×1920 (9:16), and 1920×1080 (16:9).

The manifest in `docs/images/gallery/manifest.json` records the recipes,
input hashes, renderer fingerprint, per-example thumbnail presentation recipe, and output
hashes. The fingerprint normalizes text line endings so Windows and Unix checkouts agree. Unchanged
examples are cached independently of their thumbnail presentation, so changing
the surround does not rerender the photographs. `--check` verifies the committed
files without rendering or writing. CI runs that check.

## Sources and supplied text

- Landscape: `docs/images/demo-source-final.jpg`, 2048×1365, owner-supplied
  and previously approved for publication. C/D read the existing Sony α7C
  capture information; no values were added.
- Portrait: `docs/images/demo-portrait-source.jpg`, 1000×1500, owner-supplied
  and previously approved for publication. The gallery-label text reuses the
  existing README wording, `Praha` and `Prague · Czech Republic`.
- C/D sidecar examples: the synthetic chart in `docs/examples/scan.png`
  and its existing JSON sibling. These are not a camera photograph.
- D/caption wording reuses `Berlin, Germany | October 2022`; F reuses
  `Berlin, Germany` on the left and `October 2022` on the right, with explicit
  blank-corner demonstrations. No text is inferred from the photographs.
- The signature is the owner's selected sample 3, placed bottom-right at
  width 0.12. The owner explicitly approved its use in the public README on
  2026-11-06. It is a supplied transparent PNG; no font or generated signature
  is involved, and it is not bundled with the installed renderer.

Text labels and signatures remain separate examples. H still rejects
signatures. See `docs/images/gallery/README.md` for the artwork credits.
