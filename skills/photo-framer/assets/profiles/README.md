# Bundled color profile

`srgb.icc` is the sRGB profile the renderer embeds in its own outputs (previews, share JPEGs, and
photos that arrive without a profile) and uses as the reference space for decorative colors.

- **Origin.** The profile built into LittleCMS, as returned by Pillow's
  `ImageCms.createProfile('sRGB')` (ICC v4.4, 588 bytes). Its description reads "sRGB built-in" and its
  copyright tag reads "No copyright, use freely". No third-party profile is copied.
- **Only one thing was changed.** LittleCMS stamps the current second into the header's creation
  date (bytes 24-35), so a profile built at run time differs from one second to the next. The date
  is fixed here at 2026-11-05 00:00:00, which makes every output reproducible byte for byte.
- **Checked across builds.** The bytes are identical for LittleCMS 2.15 (Pillow 10.1) and 2.19
  (Pillow 12.3), apart from that date; a regression test compares the bundled file with the profile
  the installed Pillow builds, ignoring the date.

To rebuild it:

```python
import struct
from PIL import ImageCms

profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
fixed = profile[:24] + struct.pack('>6H', 2026, 11, 5, 0, 0, 0) + profile[36:]
open('srgb.icc', 'wb').write(fixed)
```
