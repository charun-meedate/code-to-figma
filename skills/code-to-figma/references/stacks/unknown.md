# A stack with no playbook

You will hit one. The method still works, because the Figma side never
depended on the framework: it consumes token values, component names, images
and a route graph. Only the extraction of those four is stack-shaped, and
extraction is a conversation plus a regex.

Do not guess your way through this. Guessing produces a Figma file that is
confidently wrong, which is worse than one that is visibly incomplete.

## Ask for five things

1. **How do I run the product?** The command, and anything it needs to start.
2. **Can anything render one component to an image?** A test framework, a
   preview tool, a screenshot script — anything at all, however manual. The
   answer decides whether screens are in scope.
3. **Which one to three files hold the design tokens?** Colours, spacing,
   type. If the answer is "there aren't any", that is itself the finding, and
   the programme's first deliverable.
4. **Show me the smallest representative component.** One file. It tells you
   how components are declared, named and structured.
5. **Where does navigation live?** Only if flows are in scope.

Five answers, one message. Then work.

## Derive the extractor with the human watching

1. Read the token files they named.
2. Write a regex with named groups `name` and `value`.
3. Run `extract_tokens.py` with it.
4. **Show the count and five samples back and ask if they are right.**
5. Write the confirmed pattern into the profile. From here on this stack is
   configured, and later sessions do not re-derive it.

Step 4 is not politeness. A regex that matches 40 of 60 tokens looks
identical to one that matches all 60 until somebody who knows the file reads
the samples.

The same approach handles component names for the drift check: find how a
component is declared in the file they showed you, write the matcher, confirm
the count against a directory listing.

## What does not change

- **Acceptance criteria before drawing.** The A/B/C/D structure is not
  framework-specific — only the file paths in §A are.
- **One approved pilot before scaling.** More important here, not less: on a
  familiar stack a wrong approach is wrong in a way you can predict, and here
  it is not.
- **Registry as truth**, stop-and-ask on a missing ID, deviation log with
  nothing undocumented.
- **Values from source, images only to confirm.** `‹MEASURING›` for anything
  not yet measured.
- **Never fix the product's bugs in the design artifact.**
- **Tokens work.** Whatever the stack, values are in files and files can be
  parsed. Start there — it is the tier that always succeeds and it earns the
  trust to do the rest.

## Grade the evidence honestly

Most unfamiliar stacks land on real-app capture or code reading rather than a
catalog. That is fine, and it must be written into the acceptance criteria's
evidence statement. See `evidence-without-storybook.md`.

## Leave the stack easier than you found it

At the end, write what you learned into a new `references/stacks/<name>.md`
following the shape of the others: token sources with their patterns, catalog
situation, capture mechanism and scale, flow-tracing entry points, and
anything that surprised you. Offer it back to this repository.

That is how the coverage grows — every unfamiliar stack costs one conversation
once, and nobody pays it twice.
