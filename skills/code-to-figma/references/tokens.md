# Tokens — the part a machine can finish

This is the cheapest, most valuable and most verifiable leg of the whole
pipeline. It needs no screenshots, no catalog and no harness: token values
come from source files, and Figma variables can be read back and compared
value for value. On the proven run this produced **138 of 138 tokens matching
in name and value** — 95 colours and 43 numbers, alphas included.

It is also the leg that reads the codebase most thoroughly, which is why it
finds things nobody was looking for.

## Contents

- The method
- Never report a count
- What the push finds out about the codebase
- Names
- Automation, honestly

---

## The method

1. **Extract from code.** `extract_tokens.py --config … --root … --resolve-aliases`
   with a preset or regex per family, from the token table discovery produced.
   Check the count and five samples against the file before going further.

   Two options carry most of the real world. **`--resolve-aliases`** follows
   `var(--x)`, `{a.b.c}` and dotted identifiers like `AppPalette.neutralLevel00`
   to the value they end at, then evaluates the `calc()` that leaves behind —
   on real codebases most entries are references, and one web project went from
   43% comparable to 100% with this flag alone. **`format: "json-tree"`** walks
   a nested theme dumped to JSON, joining the key path, which is what a nested
   Tailwind or MUI config needs; a regex over one keeps only the leaf key and
   drops collisions silently.

   Each resolved entry keeps `aliasOf`. Use it: the semantic layer should
   become Figma variables that **reference** the primitives, not flattened
   copies of them.

   **Write the confirmed source objects into the profile** under
   `tokens.families[*].sources[]`. A later session then runs
   `extract_tokens.py --profile <profile> --root .` and repeats the extraction
   instead of re-deriving it — which is otherwise done from scratch every time,
   slightly differently.
2. **Create the variables in Figma.** Collections mirroring the families,
   names mirroring the code (`textPrimaryInverse` → `text/primary-inverse`,
   `spacing16` → `spacing/16`), scopes set so the picker stays usable.
   Record every variable key in the registry as you create it.
3. **Dump them back out** and write the dump to a file. Read the values back
   from Figma — do not assume the write did what you asked.

   Use the plugin API: `getLocalVariablesAsync()`, then for each variable keep
   `{name, resolvedType, valuesByMode}`. **This is the only method that
   enumerates a collection.** The MCP variable-defs call takes a node id and
   returns only the variables that node consumes — reaching for it because it
   is cheaper produces a partial dump, and every variable it did not see is
   then reported as missing.
4. **Diff.** `token_diff.py --code … --figma …`. Exit 0 or it is not done.

## Never report a count

Two sets can have the same number of tokens, the same names, and different
values. A count check passes every time. So does a colour check that reads
only r, g and b — on the proven run a first diff reported five overlay alphas
as missing when every one was present and correct, and the "limitation of
Figma" it seemed to prove did not exist.

`token_diff.py` compares normalized values including alpha, and prints both
sides of every mismatch. Attach its output. A sentence saying "all tokens
match" is not evidence; the report is.

Watch the encoding difference: a literal written `0xAARRGGBB` is alpha-first,
a literal written `#RRGGBBAA` is alpha-last, and Figma stores four floats. The
script normalizes all three, which is exactly the kind of thing to get wrong
by hand.

## What the push finds out about the codebase

Being forced to read every value is an audit nobody scheduled. On the proven
run it surfaced three things, all still true after the Figma work was paused:

- **A token named `size12` whose value was 10.** The name lied. Figma got 10,
  because the rule is to document what the code does — and the mismatch became
  a finding for the developers.
- **One of 34 text styles was empty** — no size, no weight — yet used in two
  production places through a copy-with. Those two call sites had no
  typography token at all. There was nothing to represent in Figma, which is
  how it was noticed.
- **No shadow token layer existed**, while shadows appeared inline across
  twenty files. The handful of effect styles created in Figma were a
  consolidation of scattered values, and saying so was part of the delivery.

Record all of it in the findings document. **Do not fix any of it here.**

## Names

Match the code's names, not a design taxonomy. The reason is practical: a
developer holding an identifier should find the variable by typing what they
already know. Where the mapping is not mechanical, put it in the explicit map
rather than relying on a loose match — `token_diff.py` reports every loose
match and asks for exactly that.

## Automation, honestly

Pushing values from code into Figma works and is exact. Running it
**unattended in CI** is a different question and the answer, as of the proven
run, was no: the plugin API needs a logged-in session, and the REST endpoint
for variables is gated behind an enterprise plan. Do not promise a nightly
sync without checking the plan tier first.

The middle step that needs neither: **export the code's tokens to a committed
file** (W3C DTCG `tokens.json` is the obvious format) and diff *that* in review.
It makes token changes visible in a merge request immediately, with no Figma
access at all, and it gives CI something to check drift against later. It was
the recommendation coming out of the proven run and it is still the cheapest
thing on this page.

If the project already has `figma-token-export` wired up, that tool owns the
Figma→code direction. Decide which direction is authoritative before either
runs; two pipelines writing the same values in opposite directions is worse
than neither.
