# Text in scripts Figma cannot break

Applies to Thai, Lao, Khmer and Burmese — scripts written without spaces
between words. Not needed for CJK, which Figma breaks acceptably.

## The problem

Figma ships no line-break dictionary for these scripts. Given raw text it
breaks at an arbitrary character, which lands mid-word and reads as a typo to
anyone who speaks the language. It also means the wrap points in the Figma
frame differ from the app's, so the paragraph is a different height and the
image diff lights up for a reason that has nothing to do with the design.

## The fix

Insert zero-width spaces (U+200B) at legal break points before the text goes
into Figma. ZWSP has no width, so nothing measured changes — only where the
renderer is *allowed* to break.

```bash
echo '["…","…"]' | python3 scripts/segment_text.py --locale th_TH
```

Returns `{original: segmented}` for the strings that changed. Paste the
right-hand side. Run it over every string, every time you add or edit copy.

## Line breaking, not word segmentation

This is the correction that matters, and it is worth understanding rather than
copying.

The first version used ICU **word** segmentation. It worked, and it left a
whole class of mismatches open: layout engines break these scripts using ICU
**line breaking**, which permits breaks *inside* what word segmentation calls a
single word. The Thai compound `ออกไป` is one word to a word segmenter and two
break opportunities to a line breaker.

The consequence was measurable: long paragraphs came out one line longer in
Figma than in the app, pushing those frames from 1–3% difference to 5–8%. It
was logged as an accepted deviation because the pre-approved list covers wrap
differences — and it did not have to be. Switching to line breaking closed the
whole class.

`segment_text.py` uses line breaking by default. `--words` restores the old
behaviour if you ever need to compare the two.

## Never segment text that is deliberately unbreakable

A fixture that exists to demonstrate a layout bug — a long unbroken string
that overflows its container — **loses the bug the moment it gains a break
point.** Segmenting it is not a fix; it is deleting the evidence.

The distinction, which took a correction to get right:

- **Segment** paragraphs that genuinely wrap in the product.
- **Leave raw** single-line text that the product clips or truncates.

The test is what the real thing does, not what the string looks like. The same
sample string can need segmenting in one screen and not in another, because
one puts it in a wrapping paragraph and the other in a clipped single line.

## Still forbidden

- **Resizing a text box** to force the break points to match the reference.
  The box takes the size the code gives it.
- **Typing manual line breaks.** They are invisible in review and wrong the
  moment the copy changes.
- Chasing a break that still lands elsewhere after segmenting. That is the
  pre-approved deviation; stop there.

## Two things to know about ZWSP

It travels. Text copied out of Figma carries the invisible characters with it,
so anyone pasting a string from the design file into code gets them too. Say
so in the deviation log — it is harmless and confusing in equal measure.

And segmenting is idempotent: the script skips any string that already
contains a ZWSP, so re-running over a whole file is safe.

## Other scripts

`--locale` takes `th_TH`, `lo_LA`, `km_KH`, `my_MM`. The break iterator comes
from PyICU where it is installed, and from macOS CoreFoundation otherwise —
the same ICU implementation the operating system uses. If neither is
available the script stops and says so rather than falling back to a
hand-written rule: a wrong break point looks exactly like a typo in a design
review, and nobody would trace it back here.
