# tokens-pair

The eval-02 fixtures, deliberately kept **away from `scripts/`**.

When they sat next to `token_diff.py`, the baseline agent found the script,
ran it, and caught the mismatches without ever reading the skill — so the eval
measured nothing. Here there is no script in sight, and the agent has to decide
how to compare on its own.

`code-tokens.json` and `figma-dump-count-trap.json` have the **same seven token
names and the same count**. Two values differ: `spacing/16` holds 14, and
`overlay/scrim` has lost its alpha while r, g and b stayed correct.
