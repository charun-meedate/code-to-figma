# The control files

Seven files in `{{controlDir}}` (default `docs/design-mirror/`). They are not
documentation of the work — they **are** the work's memory. Your context will
be compacted at least once in any programme worth running; these files are
what is left when it is.

Instantiate from `templates/`. Fill placeholders from `project-profile.json`.

| File | Created | Written by | Read by |
|---|---|---|---|
| `project-profile.json` | intake | discovery + intake | session ritual step 2 |
| `GROUND-TRUTH-RULES.md` | intake | agent, grows during work | session ritual step 1, in full |
| `acceptance-criteria.md` | intake, **unsigned** | agent, signed by leads | reviewer |
| `deviation-log.md` | intake | agent, approved by lead | reviewer |
| `screen-checklist.md` | when the frame list is enumerable | agent | the human, for progress |
| `flow-edges.json` | flows tier, from the router trace | agent | the line generator only |
| `figma-node-registry.json` | at the first Figma write | agent, after every create | session ritual step 3 |

Four exist at the end of intake. The other three appear when there is
something true to put in them — a checklist with estimated counts is worse
than no checklist.

## Contents

- The session ritual
- Why the registry is the truth
- The deviation log carries the honesty
- What survives

---

## The session ritual

Written as §0 of the rules file because it must be read before anything else:

1. Read `GROUND-TRUTH-RULES.md` to the end.
2. Read `project-profile.json` — it holds the file key, the token sources and
   every decision already made, so nothing gets asked twice.
3. Read `figma-node-registry.json`.
4. `get_metadata` on the Figma file; confirm the registry's IDs still resolve.
   **A missing ID means stop and ask.** Never recreate silently — a human may
   have moved or deleted it deliberately, and a silent recreate leaves two of
   everything with no way to tell which is live.
5. Read `screen-checklist.md` to find the resume point.
6. Load the `figma-use` skill before the first `use_figma` call.

Keep this list identical in three places — here, §0 of the rules template, and
SKILL.md. A ritual that differs between the file that states it and the file
that performs it is not a ritual.

**Conditional placeholders.** Templates use `{{IF_SEGMENTATION: …}}` for text
that only belongs when the profile turns a feature on. Keep the inner text and
drop the wrapper when the condition holds; delete the whole span when it does
not. Never ship the `{{IF_…}}` syntax into a live control file.

## Why the registry is the truth

It holds every node, variable, style, component, image hash and frame ID the
programme created, plus:

- **`source`** on each collection — the code file the values came from. A
  collection with no source is a collection somebody typed by hand.
- **`log`**, append-only — discoveries *and* mistakes. "We tried X, it silently
  did nothing" is worth more to the next session than another success line.
- **`nextSession`** — the baton. Where to resume, what to build first, what is
  still missing, and the one thing not to forget.

Two rules that cost time to learn:

**Write to it after every create, not at the end of the phase.** A session that
dies with ten nodes created and none recorded has produced ten orphans.

**Named versions are a human action.** `saveVersionHistoryAsync` is not
available through the plugin API. Ask for a named version at each phase
checkpoint. Recovery is the registry plus the checklist, not Figma's version
history.

## The deviation log carries the honesty

Three tables, and the distinction between them is the point:

- **A — pre-approved.** Signed once in the criteria. Never re-logged per screen.
  Keep it short; a growing §A is criteria being loosened to make work pass.
- **B — real product bugs, reproduced on purpose.** Not deviations. Each needs
  an annotation on the canvas so nobody reads it as a Figma mistake.
- **C — deviations found while working.** Nine columns, including who approved.

Conventions that matter more than they look:

- **Strike through a retired row, never delete it.** The log records when a
  call was wrong and when it was corrected. Deleting the row destroys exactly
  the information that makes the log trustworthy.
- **When the code's value and the rendered value disagree, take the rendered
  one, log the disagreement, and tell the developer.** On the proven run a pin
  box declared `width: 56`; six of them exceeded the available width, so the
  real render was 48. The declared number had never once taken effect. That is
  a finding about the product, discovered only because someone had to draw it.
- **An artifact of the capture harness is not a product truth.** When the
  export substitutes a placeholder asset or injects a debug message, draw what
  the *product* does and log the divergence.

## What survives

If the design system is later restructured and the Figma output is rebuilt,
these files still hold: the findings about the product, the decisions and why
they were made, and the record of what was tried and did not work. On the
proven run the programme was paused and its merge requests cancelled — and the
findings, the harness and the recorded lessons were what everyone agreed was
worth keeping.
