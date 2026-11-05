# Capture sidecar example

`scan.png` is an original synthetic color chart, generated locally from geometric
shapes for this example. It is not a photograph or a scan from a real camera.
The typed capture values in `scan.png.json` reuse the README's existing film-scan
CLI example; they do not claim to describe how the chart was photographed.

Run from the repository root:

```sh
python skills/photo-framer/scripts/frame_photo.py docs/examples/scan.png --style C --capture-sidecar --share --out-dir output/sidecar-example
```

The chart has no EXIF/XMP. The JSON supplies display text only and never creates
camera EXIF or selects a logo. Add `--iso 800` to override that field for the
whole batch; the other fields still come from each image's own JSON.

The example and chart are covered by the repository's MIT license.
