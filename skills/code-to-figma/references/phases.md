# The pipeline, phase by phase

Two of these are gates that stop the work rather than steps that advance it:
**P0 does not end until the acceptance criteria are signed**, and **P5 does not
begin until one pilot has been approved by a human**. Everything else is
mechanical once those two hold.

Phases are cumulative per scope tier. Tokens-only runs P0, P1 and P7 and
nothing else. Flows-map runs P0, P6 and P7.

---

## P-1 · Build the catalog

Only when the intake said to build one. **This is a separate project, not a
step** — days of work, and P0's evidence gate cannot pass until it has
produced images.

Flutter: hand it to `flutter-widgetbook-catalog`, then
`flutter-catalog-page-stories`. Anything else: `storybook-generic.md`, whose
four requirements are this phase's exit condition — documented stories, a
two-way name-based drift check, an image of every story, and gates that
actually run.

Do not start P0 until an image of every story in scope exists.

## P0 · Gates

Nothing is drawn during this phase. You are proving the work is possible
before spending a day discovering it is not.

**Which gates apply to which tier:**

| Gate | tokens | flows-map | components | screens / flows |
|---|---|---|---|---|
| 0 Figma file | ✔ | ✔ | ✔ | ✔ |
| 1 Font | ✔ | — | ✔ | ✔ |
| 2 Script | if non-Latin | — | if non-Latin | if non-Latin |
| 3 Evidence + scale | — | — | ✔ | ✔ |
| 4 Criteria signed | ✔ | ✔ | ✔ | ✔ |

0. **Figma file gate.** `figma.fileKey` is in the profile, and `get_metadata`
   on it succeeds. Nothing downstream has an argument to run with otherwise.
   If the file is to be created, create it here and record the key.
1. **Font gate.** The families and weights the code uses must exist in the
   Figma file. Enumerate what is actually available — the plugin API's
   available-fonts call — and match against the weights found in D7.
   **Weights are numbers in code and names in Figma**: 400 is "Regular", 500
   "Medium", 700 "Bold", and a variable font may expose named instances rather
   than each weight separately. Check what the family actually offers.
   **If a font or a weight is missing, stop and wait for it to be uploaded.
   Never substitute a similar one.** Every metric downstream — text width, wrap
   points, the image diff — is measured against the wrong thing otherwise.
2. **Script gate** (non-Latin only). Render a sample string in that font in
   Figma and look at it: tone marks, stacked vowels, the right letterforms.
3. **Evidence gate** (components and up). Confirm the reference images exist,
   are complete, and are not mid-regeneration. Calibrate the scale factor here
   — measure one known element, set `scaleCalibrated`. On a tier that produces
   no images, `scaleCalibrated: false` is the correct final state, not a gap.
4. **Criteria signed.** `acceptance-criteria.md` filled in and the signature
   table completed. Until then, "matches the code" means whatever the reviewer
   feels on the day, and reviews become taste arguments.

**If the signature does not come.** Do not block indefinitely and do not
proceed as though it arrived. Draw the pilot only — one screen or one
component — record a row in deviation §C saying the criteria were unsigned at
the time of drawing, and **hard-stop before P5.** The pilot is cheap enough to
redo; the scale phase is not.

Record each gate in the table at the bottom of GROUND-TRUTH-RULES.

## P1 · Foundations

1. **Variables first**, in collections that mirror the token families —
   typically one collection for colour (with a mode per theme) and one for
   numbers. **Set each variable's scopes** (where Figma is allowed to offer
   it). Leaving everything "all scopes" makes the picker unusable at the exact
   moment the file starts being worth using.
2. **Text styles and effect styles**, named **exactly as the code names them**.
   Do not translate a code name into design vocabulary. The point is that a
   developer can find the style from the identifier they already have.
3. **Foundation sheets** — a page showing every token with its name and value.
   This is what a designer opens; it is also how a human spot-checks the diff.
4. **Run `token_diff.py`.** N/N value-exact, or the phase is not done. Attach
   the report; do not summarize it.

   If the file already held variables this programme does not own — an org
   library, an earlier effort — they surface as "extra in Figma" and the gate
   can never go green. Waive them explicitly with `ignoreFigma` in the map
   file and **list what was waived and why in the P1 report.** Waiving
   silently is how a stale variable outlives everyone who remembers it.

Variables are the highest-value part of the whole programme and the only part
a machine can do end-to-end. Components always need a human decision.

## P2 · Assets

Upload only what the pilot needs. Real asset files — never a redraw. Vector
assets import as vector trees; raster assets become image fills. Record every
`imageHash` in the registry: a re-upload of the same file produces a different
hash and a duplicate.

Some formats are not accepted and must be converted. Converting is fine;
converting silently is not — it goes in `deviation-log.md` as **pre-approved
row A/P6** (that is a row label, not phase 6; keep that row in the template
whenever any asset was converted).

## P3 · Component kit

Still only what the pilot needs. Building the whole kit before one screen has
been validated means building the whole kit wrong.

For each component: master with auto-layout mirroring the real structure,
every fill and stroke bound to a variable, every text on a style, named after
the class. Anything that must genuinely change size becomes a **variant** —
size cannot be overridden inside an instance (see `figma-traps.md`).

## P4 · Pilot — the approval gate

**One** screen, or one component at tier 2, end to end: master, every state
frame, image comparison, audit, deviations logged, instance placed, registry
updated.

Then stop and ask for approval. Show the diff reports and the deviation rows.

The reason is structural: if the approach is wrong, it is wrong identically on
every screen. On the proven run the pilot came back approved *with a
correction* — a placeholder asset that had to become a real one. Catching that
on one screen instead of sixteen is the whole return on this phase.

Do not start P5 while the answer is outstanding.

## P5 · Scale

Batch by **evidence-base section**, not by route order — it keeps the reference
images you need in one place and stops you paging back and forth.

Per screen, the eight-condition DONE from the checklist. Update the registry
as you go, not at the end: your context will be compacted and the registry is
what survives.

### P5.5 · Cross-cutting fixes

Things discovered during P5 that apply to every screen already built — a
segmentation pass over every text node, a component fix that propagates. Two
consequences: an already-approved screen can be silently changed by a
component fix, so **tell the human when that happens**, even when the change is
an improvement; and a fix that touches every frame invalidates every diff
number taken before it.

## P6 · Flow lines

Only when every frame exists and has stopped moving. This is a deliberate
wait, not a delay — moving one frame invalidates every line, and lines are
regenerated wholesale rather than repaired. *(On the flows-map tier there are
no frames, only placeholder node cards; place them, then proceed.)*

1. Trace the router into `flow-edges.json`. Every edge carries `src` as
   `file:line`. An edge with no source is a guess and does not go in.
2. Place nodes on the grid from `meta.layout` so the canvas reads in flow order.
3. Generate every line from the JSON in one pass. Draw the legend.
4. To change anything: change the JSON, delete all lines, regenerate.

**No line generator ships with this skill — you write it, once, as part of
this phase.** It is plugin code that reads `flow-edges.json`, places the nodes,
and draws one vector per edge. Two conventions make step 4 possible at all:

- **Name every node the generator creates `flow-line/<from>--<to>`** (and the
  legend `flow-line/LEGEND`). "Delete all lines" needs a selector; without a
  naming convention there is no way to tell a generated line from anything else
  on the page, and regeneration becomes manual cleanup.
- **Decide the anchor rule once** — which edge of a node a line leaves from and
  arrives at, given the grid direction — and write it into the generator's
  header comment. Re-deriving it per edge produces a canvas that looks
  hand-drawn, which defeats the point.

Use `createVector()` with per-vertex stroke caps — a line's `strokeCap` puts an
arrowhead on both ends.

## P7 · Verify and hand off

- Every checklist row closed, or listed as not done with a reason.
- Deviation log closed: every row has a reason and an approval.
- Audit across the file: no raw hex, no unstyled text.
- Registry current; a named version saved in Figma (a human does this —
  `saveVersionHistoryAsync` is not available to the plugin API).
- A handoff note: where the work stopped, what is deliberately not done and
  why, what the next session should read first, and **which decisions you took
  on the human's behalf.** That last list is the one people forget and the one
  that matters most.
