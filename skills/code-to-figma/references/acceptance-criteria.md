# Turning "matches the code" into something you can actually check

## Why "pixel perfect" is the wrong promise

Figma and every UI framework use different text rasterizers, different
line-break dictionaries, and different ways of distributing leading. Two
renders of the same design will never superimpose exactly. If a review is run
expecting that, **not one screen passes and the work never converges** — the
reviewer keeps finding real differences, the builder keeps chasing them, and
both are right.

So define the tolerance before you draw, and get it signed. That is what turns
"100% matching" from a slogan into a claim someone can verify in ten minutes.

The four sections do different jobs:

- **A** — what must be exact, measured from code
- **B** — what is agreed not to count, signed once
- **C** — what the reviewer does per screen
- **D** — what "the programme is finished" means

## Deriving §A for this project

Section A is not boilerplate. Each row names a real file in *this* codebase,
taken from the token table discovery produced. The nine rows in the template
are the general shape; what makes them useful is the citation.

Two rows are worth extra care:

**Row 4 (radius, stroke, shadow).** If a family is absent in code — no shadow
tokens, shadows written inline — say so here and cite the finding. Do not
write a criterion the project cannot satisfy; that guarantees a permanent
failing row and teaches everyone to ignore the document.

**Row 8 (frame name = class name).** This is the naming contract, and it is
the one that makes the file usable long after the programme ends. A developer
holding an identifier can find the frame; a designer looking at a frame can
find the code. Slash-grouped names in Figma mirror the code's grouping, not a
design taxonomy invented for the occasion.

## Keeping §B honest

The six pre-approved deviations are engine-level and apply everywhere. Rows 2
and 3 (line breaks and the paragraph height that follows from them) only need
the script qualifier when the product ships a non-space-delimited script;
otherwise they still apply, just less visibly.

Two failure modes to watch:

- **§B growing.** Every row added is a category of difference nobody will look
  at again. A long §B is the criteria being loosened to make the work pass.
  Each addition costs a signature for that reason.
- **§B being used to excuse a structural error.** "It's a wrap difference" is
  true for a paragraph and false for a button in the wrong place. §B covers
  *text*; it never covers geometry.

## §C is a procedure, not a vibe

Check 1 catches structural drift. Checks 2–4 catch two things check 1 cannot
see. The first is a value that is visually right and was typed by hand: a
hardcoded hex that happens to match the token passes every image comparison
ever run, and breaks the day the design system is relinked.

The second is **anything small that moved**. The image comparison aggregates
per row, so a 24px icon displaced by 4px peaks at half a percent and opens no
band — measured, at every threshold. Checks 2–4 are the only thing standing
between that and a signed-off screen. Do not skip them because the diff was
clean; a clean diff means nothing *wide* moved.

The ±2px in check 1 is at 1× — scale it if the project's frames are not.

## The evidence statement is not optional

At the bottom of the template, one sentence saying how the frames were
verified: rendered from a catalog, captured from the running app, or read from
code. A reader must be able to tell how strong the verification behind a
signature is. "Matches the code" backed by a rendered comparison and "matches
the code" backed by careful reading are both legitimate claims — and they are
not the same claim.

## Sign it before drawing, not after

An unsigned criteria document is a document written to fit whatever got built.
On the proven run the criteria were proposed and the signature lines sat empty
while the pilot was drawn; the pilot was approved anyway, and the honest
version of that history is that the criteria functioned as a *proposal* during
the pilot and only became a contract later. That worked because the pilot was
one screen. It does not scale — the point of the gate is that it comes first.
