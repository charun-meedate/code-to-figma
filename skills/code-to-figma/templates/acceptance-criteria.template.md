# {{PROJECT_NAME}} · Acceptance Criteria — the definition of "matches the code"

<!--
  Instantiated from the code-to-figma skill.
  Provenance: the reference programme's acceptance-criteria.md.
  Sections A–D scale with the scope tier chosen at intake — delete the blocks
  marked for tiers you are not doing, and record that in §D.
-->

**Status: awaiting signature.** Nothing gets drawn in Figma until the
signature table at the bottom is filled in.

---

## Why this document exists

Literal "pixel perfect" is impossible. Figma and {{FRAMEWORK}} use different
text rasterizers, different line-break dictionaries, and different ways of
distributing leading. A review that expects two images to superimpose exactly
will **fail every single screen and never converge.**

This document converts "matches the code" into checks a reviewer can actually
run in about ten minutes per screen.

---

## A. Must match exactly — measured from code, never from an image

1. **Layout structure** mirrors the real component tree — a column in code is
   a vertical auto-layout in Figma, a row is horizontal, a stack is absolute.
2. **Spacing / padding / gap** match the spacing tokens in
   {{TOKEN_SOURCE_SPACING}} — every value, no approximations.
3. **Colour** — every fill and stroke is bound to a variable whose value
   equals the token in {{TOKEN_SOURCE_COLOR}}.
4. **Radius, stroke weight, shadow** match {{TOKEN_SOURCE_COMPONENT}}.
   <!-- if a family is absent in code (e.g. no shadow tokens), say so here and
        cite the finding ID rather than inventing one -->
5. **Text styles** — family, size, weight, line-height and letter-spacing all
   match {{TOKEN_SOURCE_TYPOGRAPHY}}.
6. **Icon and asset geometry** — real asset files imported from
   {{ASSET_SOURCE}}, never redrawn by hand.
7. **Copy and mock data** are verbatim what the evidence base shows. Never
   prettified, never translated, never shortened.
8. **Frame name = the class/component name in code.** This is the naming
   contract; it is what lets a developer find the frame from the code and back.
9. **Real bugs in the product are reproduced faithfully** (see
   GROUND-TRUTH-RULES §1) and annotated as such.

## B. Not counted as a mismatch — pre-approved deviations

Signed once here. Never logged again per screen.

1. **Anti-aliasing and glyph rasterization** — different engines.
2. **Line-break positions**{{IF_SEGMENTATION: for {{SCRIPT_NAME}} text}} —
   different dictionaries. The text box keeps the size the code gives it;
   **never resize a box to chase a break point.**
3. **Total height of a multi-line paragraph** when the break points differ —
   a consequence of 2.
4. **Baseline position within ±{{BASELINE_TOLERANCE}}px** — the two engines
   distribute leading differently.
5. **Gradient banding and dithering.**
6. **Image-compression artifacts** in assets that had to be converted
   ({{ASSET_CONVERSIONS}}) — Figma does not accept every source format.

<!-- Rows 2 and 3 apply to any project. Keep the {{SCRIPT_NAME}} qualifier only
     when the product ships a non-space-delimited script. Delete row 6 if no
     asset conversion was needed. Add project-specific rows below, but each one
     costs a signature — a long §B is a sign the criteria are being loosened to
     make the work pass. -->

## C. Per-screen review — what the reviewer actually does, ~10 minutes

| # | Check | Passes when |
|---|---|---|
| 1 | Overlay the Figma export on the reference image (1:1 scale, 50% opacity) | Every **non-text** structural edge is off by no more than **±{{STRUCT_TOLERANCE}}px** |
| 2 | Spot-check 5 colours | Each is a bound variable and its value matches the token |
| 3 | Spot-measure 3 spacings | Each matches a spacing token |
| 4 | Spot-check 2 text nodes | Each uses a named text style, and the correct one |
| 5 | Frame and layer names | Frame = class name · layer names are readable |
| 6 | This screen's rows in the deviation log | Every row has a reason and is approved |

Check 1 is the one that catches structural drift; checks 2–4 are the ones that
catch a hand-typed value that happens to look right.

## D. Definition of done for the whole programme

Keep only the blocks for the scope tier chosen at intake.

**Tokens (all tiers)**
- [ ] Every token family in {{TOKEN_FAMILIES}} extracted from code and created
      in Figma
- [ ] `token_diff` reports **N/N value-exact** — the report is attached, not
      summarized
- [ ] Families absent in code are recorded as findings, not silently skipped

**Components (tier 2+)**
- [ ] Every component in scope has a master, named after its class
- [ ] Every variant that exists in code exists as a Figma variant — and no
      variant that does not
- [ ] Audit passes: no raw hex, no unstyled text

**Screens (tier 3+)**
- [ ] {{SCREEN_COUNT}} screens present, named after their classes
- [ ] {{FRAME_COUNT}} state frames present, matching the evidence base
- [ ] Every frame passes the image comparison, or has an approved deviation row

**Flows (tier 4)**
- [ ] Every connection in `flow-edges.json` drawn, with its action label
- [ ] Branching (success / failure / guard) drawn as distinct line kinds, with
      a legend on the canvas
- [ ] The canvas reads in flow order
- [ ] Every edge cites the source line it was traced from

**Always**
- [ ] Deviation log fully closed — every row has a reason and an approval
- [ ] Registry updated; a named version saved in Figma at each checkpoint
- [ ] Review passed

---

## Evidence base for this programme

{{EVIDENCE_STATEMENT}}

<!-- One of:
  "Rendered from a component catalog — every state is reachable and reproducible."
  "Captured by driving the real app. States limited to those reachable by
   navigation; loading and error states are not represented; data varies
   between captures."
  "Code reading only. No rendered reference exists. Structure is verified
   against source, not against a render — render-time surprises (a declared
   width the layout cannot honour) cannot be detected on this path."
  This sentence is not optional. A reader must be able to tell how strong the
  verification behind a signature actually is. -->

## Signatures

| Role | Name | Date | Notes |
|---|---|---|---|
| Proposer | | | |
| Design lead | | | |
| Engineering lead | | | |
