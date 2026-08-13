# Verification — read where it differs, not how much

## Contents

- The recipe
- The percentage is the least trustworthy number on the page
- Scores are not comparable across runs
- Before every verification session
- Things that look like errors and are not
- Measuring at all
- No unmeasured numbers

---

## The recipe

1. Export the frame from Figma at 1×.
2. Downscale the reference by its scale factor with LANCZOS.
3. `image_diff.py --ref … --fig … --out diff.png` — it reports mean difference,
   percentage over threshold, and **the rows that differ, merged into bands**.
   Pass `--out` every time: without it no composite is written, and step 5
   below is the whole judgement.
4. **Judge the strongest bands.** Bands are reported peak-first. A band on a
   card edge, a button edge, an input border or an image boundary is structural
   drift, at any percentage. A band on a row of text is pre-approved.
5. Open the composite. Every time.

Text rows differ because rasterizers and break dictionaries differ — that is
pre-approved. Geometry differing is never pre-approved.

**Expect a tail of weak bands on real UI, and do not classify all of them.**
Measured on twelve production screenshots: a resample round trip — *less*
difference than two real renderers produce — opens an average of 12.3 bands per
image at the old 2% row threshold, with no design change whatsoever. That is
why the default is 5%, why bands come out ranked, and why the script says how
many peak under 15%. The rule is "every band that matters lies on text", and
the count of bands is not a score.

## The percentage is the least trustworthy number on the page

On the proven run a frame scored **0.32% while a button sat 320px away from
where it belonged.** A translucent scrim covered the frame and crushed the
contrast of the difference below the detection threshold. The frame looked
like the best result of the session.

Any frame with an overlay, barrier, modal or disabled state will under-report,
always. `image_diff.py` therefore **always** runs a second pass at a
contrast-scaled threshold and tells you how many bands the first one could not
see. Take that seriously — it exists because the original failure was caught by
eye, and being caught by eye is not a process.

It used to decide whether to bother, using a contrast cutoff. Measuring twelve
production screenshots retired that: real light-theme UIs span 163–232 levels,
the lowest only three above the cutoff, so a slightly flatter product would have
warned on every frame it ever compared. The second pass is cheap; guessing when
to run it was not worth the false alarms.

## Scores are not comparable across runs

Two things move a number without the work changing:

- **A different diff script.** On the proven run one screen's numbers rose from
  0.94–1.79% to 1.70–2.43% between sessions purely because the comparison
  changed. Nothing had got worse. The script prints its version for this
  reason.
- **A cross-cutting fix.** Anything applied to every frame invalidates every
  number taken before it.

When you need to show something improved, show it structurally: "the label's
ink now starts at x=76 on both sides, and did not before". That survives a
change of tooling; a percentage does not.

## Before every verification session

The reference images are a **build output**. If a regeneration is running, files
vanish and reappear in batches — usually alphabetically — and a whole section
can be missing for minutes. On the proven run eight reference images were read
successfully and the entire section had disappeared a few minutes later, which
read as "the evidence base has no frames for this screen". It did.

Check the process is not running and the file count is stable before you diff
anything. The exact command belongs in GROUND-TRUTH §11.5, filled in from the
profile.

## Things that look like errors and are not

- **Randomized or clock-seeded content.** Screens whose text comes from
  `now()` or a shuffle change on every regeneration. Copy what the reference
  shows; do not recompute, do not sort.
- **A frame drawn at a non-standard size.** A story that overrode the surface
  is drawn inside a normal-sized canvas, with the real content in a box in the
  middle. Build the frame at its real size and **crop the reference** to match.
  Do not stretch either image.
- **Artifacts of the capture harness.** A substituted placeholder asset, a
  debug message injected by the exporter, a font fallback in the headless
  build. Draw the *product's* truth and log the divergence.

## Measuring at all

Numbers come from source. The image confirms with the eye. When you do have to
measure off an image:

- Divide by the scale factor. Every time. A forgotten ÷2 gives a component at
  exactly double size, and it is smooth enough to pass review.
- Do not measure something that overlaps. On the proven run a card's top edge
  was measured from a white row that turned out to be an illustration
  overdrawing the card — the measurement was of the wrong object.
- When the code's declared value and the rendered value disagree, the render
  wins, the disagreement gets logged, and the developer gets told.

## No unmeasured numbers

If a number has not been measured, write `‹MEASURING›`. On the proven run a
draft summary was written with two invented gate figures that were caught
before anyone read them, and the same programme reported its coverage number
wrong three times before it was replaced by a machine check. A plausible
number is the same defect as a wrong one, and harder to catch.
