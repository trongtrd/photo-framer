# Style G: Deckled Paper

Part of the [Photo Framer skill](../../SKILL.md); global rules there still apply. Menus: [menus.md](../menus.md); constants: [presets.md](../presets.md).

G presents the photograph on cotton-style paper with a subtly textured margin,
irregular torn outer edges and a soft contact shadow on a light-gray background.
Texture and edge effects stay outside the intact rectangular photo. Never apply
paper grain, fading, torn corners, blur or color effects to the photograph itself.

Use the deterministic Python renderer for single images and batches. The fixed
procedural pattern needs no AI generation, downloaded paper texture or per-image
analysis. Offer margin width, paper tone and edge roughness once for the batch.
An explicit "G default" runs directly with 2-1-1, without a preview or questions.
No text, capture details or logo is added by default. If a caption is requested,
use the exact wording with `--caption` (bundled Inter; `--font` only on request),
and keep it on the paper.
