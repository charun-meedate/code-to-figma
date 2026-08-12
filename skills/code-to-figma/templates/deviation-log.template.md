# {{PROJECT_NAME}} · Deviation Log

<!--
  Instantiated from the code-to-figma skill.
  Provenance: poppa-notes/uxui-50/deviation-log.md.
-->

Every place where Figma does not match the code or the reference image gets a
row in this file. **No undocumented deviation, ever** — if it cannot be
matched, say so. Silence reads as "it matched".

Deviation classes:

- `font-fallback` — anything caused by fonts or glyph metrics
- `wrap` — line-break positions
- `render` — a limit of what Figma can draw (shaders, animation, native widgets)
- `bug-reproduced` — a real product bug drawn faithfully on purpose, not an error
- `evidence-artifact` — the reference image shows something the real product does
  not (a stand-in asset, a harness message); draw the product's truth and log it
- `other`

---

## A. Pre-approved — signed once in `acceptance-criteria.md` §B

Never logged again per screen.

| # | Issue | Class | Reason |
|---|---|---|---|
| P1 | Anti-aliasing / glyph rasterization differs | render | Different engines |
| P2 | Line-break positions differ{{IF_SEGMENTATION: in {{SCRIPT_NAME}} text}} | wrap | Different dictionaries — the box keeps the code's size; never resize to chase it |
| P3 | Paragraph height differs when the break points differ | wrap | Consequence of P2 |
| P4 | Baseline offset within ±{{BASELINE_TOLERANCE}}px | render | Leading is distributed differently |
| P5 | Gradient banding / dithering | render | |
| P6 | Compression artifacts in converted assets | render | OPTIONAL — keep only if assets needed converting ({{ASSET_CONVERSIONS}}) |

## B. Real product bugs reproduced faithfully

Not deviations — but each needs an annotation on the canvas so no one reads it
as a Figma mistake.

| # | Screen / frame | What you see | Cause in code | Annotated |
|---|---|---|---|---|
| B1 | | | | ⬜ |

<!-- example from the proven run:
| B2 | RegisterGenderScreen / a-gender-chosen | progress bar never reaches 100% | `(stepperIndex+1)/(steps.length+1)` register_stepper.dart:18 | ⬜ |
| B10 | Foundations / spacing | token named `size12` has the value 10 | app_theme_extension.dart:136 | ⬜ |
-->

## C. Deviations found while working

| # | Screen / frame | Node | Property | Value in code / image | Value in Figma | Reason | Class | Approved |
|---|---|---|---|---|---|---|---|---|
| C1 | | | | | | | | ⬜ |

<!-- Rules for this table, learned the hard way:

  · A retired row is struck through and kept, with a reason — never deleted.
    `| ~~C11~~ | ~~…~~ | … | **Cancelled — superseded by C13** | — | ✅ closed |`
    The log records when a call was wrong and when it was corrected; deleting
    the row destroys exactly that.

  · When the code's value and the rendered value disagree, take the RENDERED
    value, log the disagreement, and tell the developer. Example from the
    proven run: a pin box declared `width: 56`, but 6 × 56 exceeded the
    available 334px, so the real render was 48. The declared number had never
    once taken effect.

  · An artifact of the evidence base is not a product truth. When the capture
    harness substitutes an asset or injects a message, draw what the PRODUCT
    does and log the divergence as `evidence-artifact`.
-->
