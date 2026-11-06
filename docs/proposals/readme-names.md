# README names and gallery organization (accepted)

Status: approved by the owner on 2026-11-06 and implemented on
`codex/readme-clarity-film-background`, together with Film's white presentation
surround. This document records the agreed display vocabulary and hierarchy.

## One naming hierarchy

Use a short human-readable name, followed by its appearance or option.
Keep A–H and every three-digit code unchanged as compatibility identifiers.
The README should lead with names and pictures; codes and CLI flags belong in
the existing menus, recipes and technical reference, rather than underneath
every thumbnail. Natural-language requests already work through the skill;
this proposal adds no CLI aliases or parsing behavior.

| Existing identity | Proposed display name | Meaning for a new visitor |
| --- | --- | --- |
| A · Floating | Shadow / Ảnh nổi | Photo with a soft floating shadow |
| B · Gallery | Gallery / Khung gallery | Frame, white mat and outer surround |
| C · Spec card | Specs / Thông số | Camera details and brand mark |
| D · Custom spec card | Specs + Text / Thông số + chữ riêng | Camera details and the user's wording |
| E · Color Echo | Color / Viền màu | Border color drawn from the photograph |
| F · Film Edge | Film / Viền phim | Dark film edges and sprockets |
| G · Deckled Paper | Paper / Giấy xé | Textured paper with torn edges |
| H · Minimal Mat | Canvas / Khung tỷ lệ | Fixed-ratio mat or thin border, with optional blur |

The letter can stay secondary in a group heading, for example
`Shadow / Ảnh nổi (A)`. A thumbnail caption then needs only the distinguishing
value: `Default`, `Narrow margin`, `Wide margin`, `Caption`, or `Signature`.
When a variant is referenced outside its group, use `Style · Variant`:
`Shadow · Narrow margin`, `Film · No text`, `Canvas · Square · Blur`.
Do not introduce separate numbered variant names.

Use the same plain option vocabulary wherever it is supported:
`Caption / Chú thích`, `Label / Nhãn`, and `Signature / Chữ ký`.
The technical reference still explains the exact differences and exclusions.

## Keep the geometry groups; simplify their contents

- Keep all eight style groups and their A–H order. C and D stay adjacent;
  their shared `Specs` name makes the relationship apparent without changing
  their separate text requirements or their existing identities.
- Keep each real appearance option in its existing style. A frame's shadow,
  film sprockets, paper edges and fixed-ratio canvas are different geometries;
  moving a variant between these groups would misdescribe the renderer.
- Use `Appearance / Hình thức` and `Text / Chữ` as the two row headings for
  A–G. E's shared-color example belongs with appearance, not with text.
- Keep H's three rows, named `Ratios / Tỷ lệ`, `Blur / Nền mờ`, and
  `Details / Chi tiết`. Use the same ratio order in its first two rows:
  4:5, 1:1, 3:4, 9:16, 16:9, original/thin border.
- Move the two C/D synthetic-sidecar examples and the two raw-camera-code
  examples out of the main style gallery into the existing technical section.
  They explain input and metadata handling, rather than a different framing
  style. Retain the examples and their reproducible recipes there.
- Keep the portrait-photo H example: it demonstrates visible layout behavior.

The result keeps the style set and the renderer contract intact, while giving
new visitors one vocabulary for choosing an appearance. Documentation recipes
remain available to users who want exact command-line settings.

## Owner approval

The owner approved these display names, the `Style · Variant` pattern,
moving the four metadata/input examples to the technical section, moving E's
fixed-color example into its appearance row, and aligning H's ratio order.

The same approval explicitly covered the separately reviewed contributor
history update. That task preserves all 57 commit trees and the v0.11.1 tag;
it does not alter the renderer or implement new CLI name aliases.
