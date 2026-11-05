# README gallery

The README has one group for each style A–H. A–G use two horizontal rows:
seven preset examples, then representative text/input options. Each preset
example changes only one menu setting from the default, so every value in
the three-row menu is visible without listing all 27 combinations. H uses
three rows: canvas ratios, blurred backgrounds, and mats/keylines/text.

The number of columns is independent for every row. Wide tables can scroll
horizontally on GitHub; each thumbnail links to a larger JPEG. The README
uses HTML tables and image links rather than custom CSS. GitHub shrinks image
and cell width attributes to fit its container, so an accessibility-hidden
nonbreaking spacer supplies an intrinsic minimum width in each image cell.
This keeps the previews readable and activates native horizontal table scrolling.

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

Larger gallery JPEGs have a longest edge of at most 1280 px; thumbnails at
most 400 px. They use the committed sRGB profile and contain no EXIF. They
are documentation previews, not full-resolution or exact-size share files.
The H renderer's actual share outputs remain 1080×1350 (4:5), 1080×1080 (1:1),
1080×1440 (3:4), 1080×1920 (9:16), and 1920×1080 (16:9).

The manifest in `docs/images/gallery/manifest.json` records the recipes,
input hashes, renderer fingerprint, and output hashes. The fingerprint
normalizes text line endings so Windows and Unix checkouts agree. Unchanged
examples are cached; `--check` verifies the committed files without rendering
or writing. CI runs that check.

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
