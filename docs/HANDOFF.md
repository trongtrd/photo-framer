# Session handoff: Photo Framer

Updated 2026-11-11. Repository: https://github.com/trongtrd/photo-framer.
Local checkout: `C:\GitHub Projects\photo-framer` (Windows, PowerShell).
Owner: `trongtrd`. Speak Vietnamese; write commits, PRs and repository docs in English.

## Read first

Read this file, then `CHANGELOG.md`, `README.md`, `skills/photo-framer/SKILL.md`
and the relevant files under `skills/photo-framer/references/`.
Repository files and live GitHub state take precedence over old chat/artifact snapshots.

| Topic | Authoritative artifact |
| --- | --- |
| Product, installation, current styles and usage | `README.md` |
| Detailed release/change history | `CHANGELOG.md` |
| Binding agent interaction, photo preservation, metadata, text and input rules | `skills/photo-framer/SKILL.md` and `references/styles/` beside it |
| Frozen choice codes, geometry, limits, typography | `skills/photo-framer/references/presets.md`, `references/menus.md` |
| Accepted short names and grouping rationale | `docs/proposals/readme-names.md` (accepted, despite its historical directory name) |
| Gallery layout, sources, rebuilding and caching | `docs/gallery.md` |
| All 91 example recipes, input/output hashes | `docs/images/gallery/manifest.json` |
| Photo/signature publication permission and artwork credits | `docs/images/gallery/README.md` |
| Updated synthetic banner and exact imagegen prompt | `docs/images/header.md` |
| Renderer architecture | `scripts/photoframer/` under the skill; entry point `scripts/frame_photo.py` |
| Test entry point and modules | `skills/photo-framer/scripts/test_frame_photo.py`, `scripts/tests/` |
| Cross-platform CI matrix | `.github/workflows/test.yml` |

## Session outcome and integration anchor

The final integration is [PR #12](https://github.com/trongtrd/photo-framer/pull/12),
from `codex/readme-clarity-film-background` to `main`. The owner explicitly
requested opening and merging this specific change, together with this handoff.
This document travels in that PR: retrieve its actual merged status, merge SHA
and latest main CI from GitHub rather than embedding a self-referential final SHA.
After PR #12 lands, no feature implementation remains in flight.

Completed work is documented in the linked artifacts, not repeated here:

- [PR #10](https://github.com/trongtrd/photo-framer/pull/10): capture sidecars,
  A/B/G labels and the owner-approved 24 MP complete-output cap.
- [PR #11](https://github.com/trongtrd/photo-framer/pull/11): H landscape 16:9,
  square/landscape blur examples and the generated gallery.
- PR #12: accepted short display names, simpler gallery labels, white Film
  presentation surrounds, and the approved regrouping. There are 87 main-gallery
  examples plus four technical examples; all 91 recipes remain supported.
- Signature choice is resolved: supplied sample 3, width 0.12, approved for the
  public README. See the artwork credits and manifest instead of asking again.
- Sony Alpha 7C is the owner's body and already supported; no camera-name expansion is pending.

The v0.11.1 GitHub Release and its tag stay exactly at
`2f64ad02db53c5aa5a1b3380cea051c6cd19b3b0`; never move them.

## 2026-11-11 follow-up: Pillow 14 maintenance and v0.13.0 release

On 2026-11-11 the owner approved three proposals together:

- A maintenance PR from `claude/festive-bohr-x6lncl`: the tests stop calling
  `Image.getdata()` (removed in Pillow 14, 2027-10-15) and `tools/golden.py`
  drops an unused `os` import. The renderer is unchanged. Merging that PR still
  needs the owner's approval for that specific PR.
- Publishing **v0.13.0** as one GitHub Release that also covers v0.12.0, created
  from the merge commit of that PR. The changelog dates v0.13.0 to 2026-11-11.
  The Claude session cannot create tags or releases (the git proxy accepts pushes
  only to its designated branch, and the GitHub tools have no release call), so
  the owner publishes it. Check the live release list rather than this note.
- Deleting the three merged `codex/*` branches and enabling GitHub's automatic
  deletion of merged head branches. These are owner actions in GitHub settings.
  `codex/capture-sidecars-gallery-labels` and `codex/h-landscape-readme-gallery`
  still carry the pre-rewrite history; never merge them to synchronize.

## Owner-only attribution: completed history operation

The owner explicitly approved the reviewed metadata-only rewrite of main.
Original main `08a191c` became `43c8281c4ba5d52bd751ded78bbc9c27a911f87b`.
All 57 commit trees and parent relationships were verified unchanged. The operation
changed 45 commit IDs, replaced 26 Claude author/committer identities, removed
33 Claude co-author trailers and removed 37 obsolete signature headers.
The existing v0.11.1 tag/release and other published branch refs were not moved.
The current development branch was rebased onto the rewritten main with its tree unchanged.

Local, ignored audit artifacts are in `output/contributors-review-2026-11-06/`:
`review.md`, `report.json`, `commit-map.json`, verified `original-history.bundle`
and isolated `preview.git`. They contain the review evidence and rollback data;
do not delete them casually or publish that backup as a new GitHub branch.
Historical SHAs in earlier artifacts refer to the original history. Old local or
remote development branches may still have that history: start future work from
freshly fetched main, never merge an old branch merely to synchronize it.

After publication, GitHub's contributor API reported only `trongtrd` (57 commits,
before subsequent integration commits). The native main-page sidebar still
showed the old two-person list including Claude at the last visual check.
[GitHub documents a refresh delay of about 24 hours](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-a-projects-contributors).
Check it again in the next session. Do not claim the sidebar is fixed until observed;
do not rewrite more history or move the release tag to work around this cache.
If it remains stale beyond the documented delay, propose a GitHub Support follow-up.
Do not send a support message without the owner's instruction.

## Verification already performed

- Windows Python 3.14.8 / Pillow 12.3.0: all 76 tests passed; the last naming run
  took about 88 seconds. Generated-doc and gallery checks passed.
- Naming/regrouping preserved all 91 image recipes and generated image bytes.
  Earlier F correction changed only its ten thumbnail surrounds, preserving the
  other 81 framed thumbnails and all 91 larger previews.
- Native GitHub verification: all 93 thumbnails loaded, previews stayed 240 px
  wide with horizontal scrolling, labels had no technical codes, Canvas ratio
  order matched across plain/blur rows, and four technical examples were relocated.
- Five CI jobs passed for the rewritten main (run 42143980539) and final naming
  branch at `9507a66` (run 42145222027). Read the final PR-head and post-merge
  main runs for the handoff commit rather than treating these prior runs as current.
- The renderer itself did not change in PR #12. The preceding renderer change
  passed golden against original `5f49b92`: 303 cases / 1,047 files byte-identical.

Recheck on takeover:

```sh
git fetch origin
python skills/photo-framer/scripts/test_frame_photo.py
python tools/gen_docs.py --check
python tools/gallery.py --check
```

Inspect local modifications before switching/updating branches. Read open PRs,
latest main checks and release/tag state. Trust the repository if anything differs.

## Working agreements that persist

- Keep A–H and the three-number codes frozen. Short display names are skill/README
  vocabulary, not new CLI aliases. Product constraints are in SKILL/presets/style references;
  follow them without reopening settled decisions.
- No new feature until the owner approves it. Do not open a PR unless requested;
  merge authorization is specific to that PR. PR #12's authorization is not reusable.
- Push only the branch designated for new session work. The one-time approved
  main-history exception is complete; no further force-push or tag changes are authorized.
- Use the owner's configured Git identity and never add AI co-author trailers.
- Include changelog, docs and applicable demos with implementation changes;
  renderer refactors must pass `tools/golden.py`.

## Remaining decisions and useful next steps

1. Verify the maintenance PR's merge, main CI, the v0.13.0 release state and the
   contributor sidebar cache (not observable from a cloud session; ask the owner).
2. Confirm the merged `codex/*` branches are gone. Preserve the
   history-review backup and the frozen v0.11.1 tag.
3. There is no other approved feature backlog. Signature selection, naming/grouping,
   sidecars, labels, output cap and landscape/square framing are resolved.

## Nonduplicated operational lessons

Near-24 MP synthetic render/share measurements on this Windows environment peaked
at A 471 MB, B 375 MB, C 557 MB, D 558 MB, E 534 MB, F 549 MB, G 514 MB and
H 9:16 blur 342 MB. These are measurements, not worst-case RAM guarantees.
For golden on Windows, resolve temporary roots to avoid 8.3 username aliases;
use filesystem-safe ratio names such as `9x16`. The tool already handles these.
Use the committed sRGB profile; its tests mask only LittleCMS date/platform
variation when comparing a freshly built profile, not when comparing output bytes.
