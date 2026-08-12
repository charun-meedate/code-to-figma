---
name: code-to-figma
description: Rebuild a codebase's design system inside Figma so it matches the running code — tokens value-exact, structure within a measured tolerance, names identical, flows traced from the router — optionally via a component catalog that supplies the rendered evidence. Use when asked to create a Figma design system, component library, screens or user flows from an existing codebase, to mirror an app in Figma, or to sync code tokens into a Figma file.
---

# Mirroring a codebase into Figma

The running code is the truth. Everything in Figma is **documentation of that
code, not a redesign** — if the product does something ugly, the Figma file is
ugly in the same way, with a note saying why. An agent's instinct to improve
what it draws destroys the entire value of the work, because the result stops
being evidence of anything.

"Matches 100%" is meaningful only against criteria signed before the first
frame is drawn. Literal pixel-perfection is impossible across two rasterizers;
what is possible, and what this produces, is *value-exact tokens, structure
inside a stated tolerance, identical names, and every difference written down.*

**This works on any stack.** The Figma side consumes four things — token
values, component names, reference images, and a route graph. Only extracting
those four is framework-specific.

## New programme, or resuming one?

If the control files already exist in the project, this is a **resume**: skip
the intake entirely and run the session ritual — read GROUND-TRUTH-RULES to
the end, read `project-profile.json`, read the node registry, `get_metadata`
the Figma file and confirm every registry ID still resolves, read the
checklist for the resume point, load `figma-use` before the first Figma call.
**A missing ID means stop and ask; never silently recreate.**

Otherwise, discover, then ask. The intake fires exactly once per programme.

## Discover before you ask

Run the read-only scan in `references/discovery.md` first: framework, token
sources per family, existing catalog, DI/router/i18n, how images can be
produced, fonts and their weights, text script. Cite a file for everything you
find; leave anything you cannot cite as unknown.

Then the intake options are "I found X — confirm?" rather than open questions.
Never ask what the repository can answer. Never assume what it cannot.

Flutter → the catalog work is covered by the two bundled skills. Web, native,
or anything else → `references/stacks/`.

## The intake

Ask before touching anything. Use `AskUserQuestion` if it is available, one
call carrying both questions; otherwise ask them as plain text and wait.

**Q1 — Build a component catalog?**
- *Reuse the existing one* — offer this pre-selected when discovery found one
- *Build one first* — recommended when screens are in scope; it is the
  measuring instrument
- *No, go straight to Figma* — fine for tokens and flows, costly for screens

**Q2 — How far?** Cumulative tiers:
- **T1 tokens** — variables, text styles, effect styles
- **T2 + components** — masters and variants for shared components
- **T3 + screens** — every screen, every state
- **T4 + flows** — the navigation graph, drawn from the router
- **flows-map** — *not* cumulative: the navigation graph alone, nodes drawn as
  placeholder cards. Code-only, no screens, cheap. Offer it whenever someone
  wants to see how the product connects without paying for screen art.

**Q3 — only when Q1 is "no" and scope is T3 or higher.** Which evidence base:
driving the real app (cannot force error, empty or edge states) or reading
code only (weakest; the acceptance criteria must say so in writing).

**Q4 — the three the repository cannot answer.** Ask these every time, even
when discovery guessed well; each was a human decision that was expensive to
get wrong:
- **Which Figma file?** A URL to write into, or permission to create one.
  Nothing downstream can run without a file key — no discovery step produces
  it, and a repository cannot know it.
- **May the organisation's existing design-system library be used**, or is this
  built standalone from code first?
- **Which build variant/flavour is the reference**, when the project has more
  than one.

On the web, add: **which breakpoints get documented**, and **which themes** —
a web product has no single frame size, and silently drawing one width is the
same defect as an unmeasured number.

An answer already stated plainly in the user's prompt can be taken — but
restate it for confirmation. **A guessed intake poisons every phase after it**,
and the cost lands hours later.

Then state the defaults you are assuming rather than asking about them:
control files in `docs/design-mirror/`, one flow at a time, light theme first.

## What each branch actually runs

| Scope | Phases | Evidence base | The honest limitation to state |
|---|---|---|---|
| **T1 tokens** | P0 (font gate), P1, P7 | source files only — no screenshots at all | "Variables are value-exact against code. Nothing is claimed about how components consume them." |
| **T2 components** | + P2, P3, P4, P5 | catalog renders, or one-off component renders | "Masters verified against renders; screen composition unverified." |
| **T3 screens** | full P0–P5.5, P7 | catalog gallery — or a degraded base, declared | catalog: structure to ±2px, text rows pre-approved. Otherwise see `evidence-without-storybook.md` |
| **T4 flows** | + P6 | the router trace | "Arrows are only as good as the trace — every edge cites its source line." |
| **flows-map** | P0 (minimal), P6, P7 | router files only | "A navigation map, not screen art. No visual claims." |

Tokens-only must run with no screenshot tooling whatsoever. A flow map needs
nothing but the router.

## The pipeline

**P-1 Catalog** (only if Q1 said build one) → **P0 Gates** → **P1 Foundations**
→ **P2 Assets** → **P3 Component kit** → **P4 Pilot** → **P5 Scale** →
**P5.5 Cross-cutting** → **P6 Flow lines** → **P7 Verify and hand off**

**P-1 comes first and is a separate project.** Building a catalog is days of
work, not a step — and P0 cannot check that reference images exist until it has
produced them. Its exit condition is the contract in `storybook-generic.md`.
On Flutter, hand it to the two bundled skills.

Two of the rest are gates, not steps:

- **P0 does not end until the acceptance criteria are signed.** Also in P0: the
  font exists in Figma at the exact weights the code uses — if it does not,
  **stop and wait for it; never substitute a similar font.**
- **P5 does not begin until one pilot screen has been approved by a human.**
  If the approach is wrong it is wrong identically on every screen.

Which P0 gates apply depends on the tier — tokens-only and flows-map never
produce images, so the image gates do not apply to them. See `phases.md`.

Flow lines come last and only once frames have stopped moving — a moved frame
invalidates every line, and lines are regenerated wholesale, never repaired.
Details in `references/phases.md`.

## The control files are the work

Seven files in the project, from `templates/`. Not paperwork — they are the
programme's memory, and your context will be compacted at least once.

`project-profile.json` (what this project is) · `GROUND-TRUTH-RULES.md` (the
rules, read at every session start) · `acceptance-criteria.md` (signed before
drawing) · `deviation-log.md` (nothing undocumented) · `screen-checklist.md`
(per-frame progress) · `flow-edges.json` (the only source of lines) ·
`figma-node-registry.json` (every ID you created).

**The registry is the truth, not your memory of it.** A session that trusts
recall over the registry recreates nodes that already exist, and now there are
two of everything with no way to tell which is live. Write to it after every
create, not at the end of the phase.

## Define "matches" before drawing

`acceptance-criteria.md` has four sections and they do different jobs: **A**
what must be exact, measured from code · **B** what is agreed not to count,
signed once (rasterization, line breaks, baseline tolerance, banding) · **C**
what a reviewer does per screen in ten minutes · **D** what finished means.

Without §B, a reviewer comparing two rasterizers rejects every screen forever
and is right to. Without §A, "matches" means whatever anyone feels that day.
See `references/acceptance-criteria.md`.

## Verify by measurement

**Tokens:** dump every variable back out of Figma and compare values one at a
time with `token_diff.py`. **Never report a count** — two sets can have the
same names, the same count, and different values, and a count check passes
every time. Colour comparison includes alpha.

**Frames:** export, downscale the reference, and read **where** it differs.
`image_diff.py --ref … --fig … --out diff.png` reports the differing rows as
bands and writes the composite you must open. **Pass only when every
band lies on a row of text**; a band on a card or button edge is structural
drift at any percentage. On the proven run a frame scored 0.32% while a button
sat 320px out of place, hidden under a translucent scrim — the script now
detects low-contrast frames and re-runs at a scaled threshold, but the rule
stands: read the bands, and open the image.

Scores from different versions of a diff script are not comparable.

## Rules that exist because they were broken

- **Never fix the product's bugs in Figma.** Reproduce them, annotate them, and
  record them in the findings document. Never touch the source.
- **Never normalize what is random.** Clock-seeded dates and shuffled options
  change on every regeneration. Copy what the reference shows.
- **Divide by the reference scale, every time.** Forget once and you get a
  component at exactly double size — smooth enough to pass review.
- **Values come from source; images only confirm.** If you have not read the
  source, you may not write that you know it.
- **Write `‹MEASURING›`, never a plausible number.** A guessed figure is the
  same defect as a wrong one and much harder to catch.
- **Never hardcode a hex or a font size.** Everything binds to a variable or a
  style, or the relink later becomes a manual sweep of the whole file.
- **Never build a convincing fake.** What cannot be drawn gets a notice saying
  what is blocking it — never a plausible-looking stand-in.
- **Never draw or hand-edit a flow line.** Change the JSON, regenerate.
- **A missing registry ID means stop and ask.**
- **An absent token family is a finding, not a gap to fill.**

## Scripts

`$S` is this skill's `scripts/` directory.

| Script | Does |
|---|---|
| `extract_tokens.py` | pulls token names and values out of source, per family, by preset or regex |
| `token_diff.py` | compares those values against a Figma variable dump; exits non-zero unless every value matches |
| `image_diff.py` | frame vs reference, reported as differing bands, with low-contrast escalation |
| `segment_text.py` | zero-width spaces at legal break points for Thai, Lao, Khmer and Burmese |
| `selftest.sh` | hermetic checks for all of the above |

`image_diff.py` needs Pillow and numpy. `segment_text.py` needs PyICU, or runs
on macOS as-is.

## References

| File | Read it |
|---|---|
| `discovery.md` | first, before the intake |
| `phases.md` | per-phase gates, pilot protocol, flow generation |
| `control-files.md` | the seven files and the session ritual |
| `acceptance-criteria.md` | writing §A–§D for this project |
| `tokens.md` | the value-exact method, and what it finds in the codebase |
| `verification.md` | the diff recipe and how numbers mislead |
| `figma-traps.md` | before the first Figma write — several traps fail silently |
| `text-segmentation.md` | non-space-delimited scripts |
| `storybook-generic.md` | the catalog contract, for non-Flutter stacks |
| `evidence-without-storybook.md` | on the no-catalog branch at screens scope |
| `stacks/flutter.md` | Flutter — the proven path |
| `stacks/web.md` | React, Next, Vue, Svelte, Angular |
| `stacks/native-mobile.md` | SwiftUI and Compose |
| `stacks/unknown.md` | a stack with no playbook |

After editing this skill, run `scripts/selftest.sh` — twice. A suite that is
green once has not been proven green.
