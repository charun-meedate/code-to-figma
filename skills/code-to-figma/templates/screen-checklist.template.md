# {{PROJECT_NAME}} · Checklist — {{SCOPE_LABEL}}

<!--
  Instantiated from the code-to-figma skill.
  Provenance: poppa-notes/uxui-50/screen-checklist.md.
  Keep the block for your scope tier and delete the others.
  Counts are ENUMERATED from the evidence base, never estimated. Until you have
  counted, write ‹MEASURING›.
-->

{{SCREEN_COUNT}} screens · **{{FRAME_COUNT}} frames** · frame list verified
against the evidence base on {{DATE}}

> ⚠ **Before every verification session, confirm the evidence base is not being
> regenerated** — see GROUND-TRUTH §11.5. During a regeneration, files vanish
> in batches and it looks like the reference for a screen does not exist.

Reference image naming: `{{NAMING_PATTERN}}` in `{{EVIDENCE_DIR}}`

---

## Definition of DONE — screens tier

A screen is done when **all eight** hold:

1. Master component created
2. Every state frame created
3. Image comparison passes on **every** frame
4. Audit passes — no raw hex, no text without a style
5. Deviations logged
6. Instance placed on the Flow page
7. Node IDs written into the registry
8. A named version saved in Figma

<!-- Components tier: conditions 6 and 8 do not apply — DONE is the other six.
     Tokens tier: replace this list entirely with the token block below. -->

## Definition of DONE — tokens tier

Per token family:

- [ ] `{{FAMILY}}` — extracted N from {{SOURCE}} → created N in Figma →
      `token_diff` reports **N/N value-exact** → report attached
- [ ] Families absent in code recorded as findings with their evidence

---

## Progress

| Phase | Status | Date |
|---|---|---|
| P0 Gates | ⬜ | |
| P1 Foundations | ⬜ | |
| P2 Assets | ⬜ | |
| P3 Component kit | ⬜ | |
| P4 Pilot — **approval gate** | ⬜ | |
| P5 Scale | ⬜ | |
| P5.5 Cross-cutting fixes | ⬜ | |
| P6 Flow lines | ⬜ | |
| P7 Verify + handoff | ⬜ | |

---

## Batch 1 — {{BATCH_NAME}} (`{{EVIDENCE_SECTION}}`)

### {{ScreenClassName}} — {{N}} frames ⬜

- [ ] `{{state-slug}}` — master `{{nodeId}}` · diff ‹MEASURING› · notes
- [ ] audit: every fill/stroke bound · every text on a style · no raw hex
- [ ] instance placed on the Flow page (`{{nodeId}}`)

> Measured values for this screen, derived from code — checked once, do not
> re-measure:
>
> | Part | Coordinates | Derived from |
> |---|---|---|
> | | | |

<!-- Frame status glyphs: ✅ done · ⬜ not started · 🔵 in progress ·
     ⚠ caveat or real-bug marker · ← cursor marking where to resume.
     Batch by evidence-base section, not by route order — it keeps the
     reference images you need open in one place. -->

---

## Counts

| Group | Screens | Frames |
|---|---|---|
| | | |
