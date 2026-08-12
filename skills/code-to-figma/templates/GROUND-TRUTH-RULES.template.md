# {{PROJECT_NAME}} · GROUND TRUTH RULES

<!--
  Instantiated from the code-to-figma skill. Generalized from a real programme
  that mirrored 16 screens / 59 frames of a Flutter app into Figma
  (provenance: the reference programme's GROUND-TRUTH-RULES.md, Aug 2026).
  Fill every {{PLACEHOLDER}} from project-profile.json before the first session.
  Delete sections marked OPTIONAL if they do not apply — but delete them
  deliberately, and say why in the Decisions section.
-->

**Read this file to the end at the start of every session, before touching
Figma.** These rules exist because they were already broken once, and because
an agent's instinct to "make it look good" destroys the value of this work.

This work is **documentation of real code, not a redesign. If the code does
something ugly, Figma has to be ugly in the same way.**

---

## 0. Session-start ritual (never skip)

1. Read this file to the end.
2. Read `project-profile.json` — the Figma file key, the token sources, and
   every decision already taken.
3. Read `figma-node-registry.json` — take the IDs you need.
4. `get_metadata` on the Figma file and confirm the registry IDs still resolve.
   - **A missing ID means stop and ask {{OWNER}}.** Never silently recreate it —
     a human may have moved or deleted it on purpose.
5. Read `screen-checklist.md` to find where the work stopped.
6. Load the `figma-use` skill before the first `use_figma` call of the session.

Your context will be compacted. **The registry file is the truth, not your
memory of it.**

## 1. Never fix the app's bugs in Figma

The reference images render real production code. Most things that look wrong
are real bugs. **Reproduce them and annotate them** — a `note` on the frame
plus a row in `deviation-log.md` table B saying "real bug in the app, not a
Figma error". New bugs found while drawing go to {{FINDINGS_DOC}} and nowhere
else. Do not touch {{SOURCE_DIR}}.

Known bugs to reproduce faithfully — fill as you find them:

| Screen / component | What looks wrong | The real cause in code |
|---|---|---|
| | | |

<!-- example from the proven run:
| SplashScreen (force update) | dialog stacked twice, barrier unusually dark | `BlocListener` has no `listenWhen` → opens twice (finding 10) |
| RegisterGenderScreen | progress bar never reaches 100% | `(stepperIndex+1)/(stepperSteps.length+1)` |
-->

## 2. Never normalize what is random

Anything seeded by a clock or a shuffle renders differently every time the
reference images are regenerated. **Copy exactly what the reference image
shows.** Do not recompute it, do not sort it, do not tidy it.

Screens with non-deterministic content in this project:

| Screen | Source of variance |
|---|---|
| | |

<!-- example from the proven run: RegisterBirthdateScreen (`DateTime.now()` at build
time), RegisterCharacterQuestionScreen (`shuffledChoices()` on every load).
A mismatch on those two after a regen is expected, not an error. -->

## 3. Frame size and reference scale

- Standard frame: **{{FRAME_W}}×{{FRAME_H}}** ({{FRAME_DEVICE}}), safe area top
  {{SAFE_TOP}} / bottom {{SAFE_BOTTOM}}.
- **Reference images are @{{REF_SCALE}}x ({{REF_W}}×{{REF_H}}) — every value
  measured off an image must be divided by {{REF_SCALE}}.** Forget that once
  and you get a component at double size, smooth enough to survive review.
- Calibrate before the first measurement: measure one element of known size in
  a real reference image and confirm the ratio. Record it in the profile as
  `screenshots.scaleCalibrated`.
- **Exceptions:** a story or screen may override the surface size. Draw it at
  its real size and crop the reference to match — never resize it to the
  standard frame.

| Screen | Real size | Crop box in the reference |
|---|---|---|
| | | |

## 4. Where the numbers come from

**Every value is read from source. Images confirm with the eye only.**

| What you need | Read it from |
|---|---|
| Colours | {{TOKEN_SOURCE_COLOR}} |
| Typography (family / size / weight / line-height / letter-spacing) | {{TOKEN_SOURCE_TYPOGRAPHY}} |
| Spacing / radius / sizes | {{TOKEN_SOURCE_SPACING}} |
| Stroke weight / shadow | {{TOKEN_SOURCE_SHADOW}} — write "absent, finding {{id}}" if there is no token layer |
| Where a screen goes when something is tapped | {{ROUTER_FILES}} |
| Which states a screen has | {{STATE_SOURCE}} |

If you write "measured", you must have measured. **If you have not read the
source, you may not write that you know.** Write `‹MEASURING›` in place of a
number you have not taken yet — a plausible number is the same defect as a
wrong one.

## 5. Never build a convincing fake

Anything Figma genuinely cannot do — shaders, animation, native pickers, live
data — gets:

- a `note` on the node saying plainly that it is a still frame or an
  approximation, and why;
- a row in `deviation-log.md`.

**Never draw something that looks like the real thing and let it be read as
the real thing.** A missing image renders as a filled box with no error — it
is indistinguishable from a dark photo.

## 6. Text segmentation — OPTIONAL, keep only if {{SEGMENTATION_REQUIRED}}

Figma has no line-break dictionary for {{SCRIPT_NAME}}. Raw text breaks
mid-word, which reads as a typo.

**Every {{SCRIPT_NAME}} string must pass through the segmenter before it goes
into Figma:**

```bash
echo '["…","…"]' | python3 {{SKILL_PATH}}/scripts/segment_text.py --locale {{LOCALE}}
```

It returns `{original: segmented}` for the strings that changed. Put the
right-hand side into Figma. ZWSP is zero-width, so widths and layout are
unaffected.

**Exception — never segment text that is deliberately unbreakable.** A fixture
that exists to demonstrate a layout bug loses the bug the moment you segment
it. The principle: segment **paragraphs that should wrap**; leave **single-line
text the real app clips** exactly as it is.

Still forbidden: resizing a text box to force the break points to match the
reference; typing manual line breaks. If the break lands elsewhere after
segmenting, that is an accepted deviation (P2) — stop chasing it.

## 7. Scope — what this programme does not do

{{NOT_DOING_LIST}}

<!-- e.g. dark theme · screens outside the chosen flow · tablet / large text scale ·
prototype animation · publishing the library · fixing app bugs · touching source -->

## 8. Token discipline

- Every fill and stroke binds to a variable. Every text node uses a text style.
- **Never hardcode a hex value or a font size. Not once.**
- Failing the audit means the screen is not done, no matter how right it looks.
- Reason: when the design system is restructured, a fully bound file is a
  mechanical relink. One hand-typed colour turns it into a manual sweep of the
  whole file.

## 9. Decisions already settled — do not re-litigate

| Decision | Why |
|---|---|
| {{LIBRARY_POLICY}} | |
| | |

<!-- example from the proven run:
| Do not convert the web build of the catalog into Figma | Flutter web renders to a single `<canvas>`; the result is a flat bitmap with no layers. Settled — do not retry. |
| Build locally from code first, relink to the org design-system library later | Owner's call. |
-->

## 10. Flow lines

- Every line is generated from `flow-edges.json`. **Never draw one by hand,
  never edit one by hand.**
- A frame moved → delete all lines and regenerate. One command.
- To change the flow, change the JSON first, then regenerate.
- Do not draw lines until the frames have stopped moving. Lines drawn early
  are lines you will delete.

## 11. Limits hit while working — do not retry these

Figma plugin-API traps are stack-independent and live in the skill:
`references/figma-traps.md`. Read it before the first Figma write of the
programme.

Traps specific to **this** project, found as you go:

| What was tried | Result | What to do instead |
|---|---|---|
| | | |

## 11.5 Check the evidence base is not being regenerated

{{EVIDENCE_DIR}} is a build output. If a regeneration is running, files
disappear and reappear in batches, and a diff against a half-written file
produces a phantom failure.

**Before every verification session:**

```bash
{{REGEN_CHECK_CMD}}
```

If it is running, wait. Do not diff.

## 12. Things Figma already has — do not draw them

| What you need | Use this |
|---|---|
| Icon fonts already installed in Figma | Create a text node and type the ligature name at the code's size — a real glyph, not a redraw. Match the icon family to the suffix used in code. |
| The project's own icons | Upload the real asset files ({{ICON_SOURCE}}) with `upload_assets` and import as a vector tree. Never redraw. |

## Gate status — update when each one passes

| Gate | Status | Notes |
|---|---|---|
| Font {{FONT_FAMILY}} present in Figma with weights {{FONT_WEIGHTS}} | ⬜ | |
| {{SCRIPT_NAME}} glyphs render correctly in that font | ⬜ | OPTIONAL — non-Latin scripts only |
| Acceptance criteria signed | ⬜ | `acceptance-criteria.md` |
| Pilot {{PILOT_TARGET}} approved | ⬜ | unlocks the scale phase |
