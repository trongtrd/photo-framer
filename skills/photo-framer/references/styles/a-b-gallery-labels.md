# Styles A/B: optional gallery labels

Part of the [Photo Framer skill](../../SKILL.md); global rules there still apply.

`--title` and optional `--subtitle` add the same centered gallery label as H:
Inter SemiBold in near-black, followed by smaller gray Inter Regular. Read the
user's exact wording; never infer it from metadata, filenames, or the photo.

The photo keeps its size and top-left position. Only the lower surround (A),
or the lower white mat and enclosing frame (B), grows as needed. The label
stays within the photo's left/right edges. Long text is rejected instead of
being shrunk, cropped, wrapped, or rewritten.

Choose a gallery label, an ordinary `--caption`, or a PNG `--signature`
separately. Do not combine the centered label with a corner signature: this
keeps the balance that led to the owner's no-signature rule for H.
Existing unlabelled choice codes keep exactly their previous geometry.

All framed outputs, including the enlarged label band, must fit the shared
24 MP cap. A size rejection asks for a smaller source copy; it never resizes
the photo silently.
