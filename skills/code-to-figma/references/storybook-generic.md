# The catalog contract

**Flutter: stop here and load `flutter-widgetbook-catalog`, then
`flutter-catalog-page-stories`.** They are the proven path and they ship in
this repo. This page is for every other stack.

A catalog is not the deliverable. It is the **measuring instrument** for the
Figma work: it renders real components with no backend, in states the running
app cannot easily be pushed into, and exports an image of every one. Skip it
and you can still do tokens and flows exactly as well — but you have nothing
to compare a screen against. That trade is spelled out in
`evidence-without-storybook.md`.

Whatever tool you use, it has to satisfy four things.

## Contents

- 1 · Every story carries documentation, enforced
- 2 · A two-way drift check, by name
- 3 · An image of every story
- 4 · Gates that actually run
- Fakes, in order of preference
- What the catalog gives back

---

## 1 · Every story carries documentation, enforced

Name, when-to-use, props, and a static overview of the variants that genuinely
exist. Not a nice-to-have: **make them required by the wrapper** so a story
cannot compile or lint without them.

`whenToUse` is the field that decides whether the catalog is useful to
designers or only to developers. If reading it does not tell you whether to
reach for this component, it is not done.

The overview shows variants **that exist in code**. Not variants that seem
likely, not variants somebody might want. The catalog's whole value is that it
cannot lie about the product.

## 2 · A two-way drift check, by name

The check that keeps the catalog honest compares **component names in code**
against **the names stories register**, in both directions:

- a component with no story → fail
- a story naming a component that no longer exists → fail
- every exclusion carries a written reason, and the excluded name must
  actually exist

**By name, never by file.** Counting story files against component files
over-reported twice on the proven run — one file can declare several public
components, and a component rendered *inside* another story is drawn without
being catalogued. Replacing the count with a name-based machine check took the
gap from a claimed zero to a real 100.

The moment the gap list is empty, the check changes job: it stops being a
backlog and becomes a **ratchet**. A new component without a story fails
immediately, and putting a name back on the exclusion list is a decision
somebody has to defend in review.

## 3 · An image of every story

This is what Figma consumes. Requirements:

- Every story, both themes if the product has them, at a fixed surface size.
- A deterministic filename that encodes the story path, so a frame in Figma
  can be traced to its reference without guessing.
- **A blank-image guard.** A story that fails to render produces a blank
  frame, and a blank frame is invisible to every other check. On the proven
  run a logo exported as empty space and looked order-dependent, because image
  decoding had not completed before capture.
- **No silent cropping.** If the exporter trims or fits, know exactly what it
  does. A trim that is right for a component grid is wrong for a screen: on
  the proven run screens exported 518px tall instead of 844 because trailing
  blank space was being cut.

Web specifics: Storybook's test-runner with Playwright is the standard path.
Freeze animations and pin fonts before capturing, or the same story produces a
different image every run and every diff is noise.

## 4 · Gates that actually run

Five, and know which is which:

| # | Checks | Typically |
|---|---|---|
| 1 | Lint / type errors | `lint`, `analyze`, `tsc` |
| 2 | Catalog tests | the catalog's own test command |
| 3 | The whole project's tests | the project test command |
| 4 | It builds | the production/static build |
| 5 | Every story screenshots | the export command |

**Gate 2 usually does not cover gate 5.** On the proven run the export file
deliberately lacked the test-file suffix so the expensive run stayed out of the
normal suite — which meant "1,613 tests passing" was true and said nothing
about whether a single image had been produced. Name the export command
explicitly, every time.

When an agent says it is green, the useful question is not "are you sure" —
it is **which gates actually ran.**

## Fakes, in order of preference

1. A fake that **throws loudly** when something unexpected is asked of it.
2. The real class with only its I/O replaced — real logic, fake network.
3. An in-memory stand-in.

Never a no-op that returns empty. On the proven run a missing image rendered
as a filled box with no error, indistinguishable from a dark photograph. If a
component genuinely cannot be rendered, **say so on the canvas** with a notice
naming the blocker and what would clear it — never a plausible-looking fake.

## What the catalog gives back

The reason this is worth doing even when Figma is not the goal: laying every
component out one at a time, in every state, surfaces things nobody was
looking for. The proven run recorded **29 production bugs** that way — including
ten places where a failed request rendered as ordinary emptiness, so a user
saw "nothing here" instead of "try again". One fix, ten screens.

Record them. **Do not fix them from this branch.** The catalog's credibility
rests on documenting what the product does; a branch that quietly improves the
product while documenting it can no longer be used as evidence of anything.
