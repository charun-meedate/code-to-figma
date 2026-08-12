# Web — React, Next, Vue, Svelte, Angular

One page, because Storybook covers all of them and the differences are in
where the tokens live, not in the method.

**Status: playbook, not proven.** The method transferred from a run on another
stack; the mechanics below are the standard tooling for these frameworks and
have not been through a full programme here. Where something is a
recommendation rather than a measured result, it says so.

## Token sources, most to least authoritative

| Shape | Where | Preset |
|---|---|---|
| **W3C DTCG** `tokens.json` with `$value` | anywhere; often `tokens/` | `dtcg-json` |
| **CSS custom properties** | `:root {}` in a global stylesheet | `css-custom-property` |
| **Tailwind** | `tailwind.config.*` under `theme.extend` | `js-object-string` / `js-object-number` |
| **MUI / Chakra** | `createTheme(` / `extendTheme(` | `js-object-string` |
| **styled-components / Emotion** | a `theme.ts` object export | `js-object-string` |
| **Panda, Stitches, vanilla-extract** | their config or `createTheme` call | `js-object-string` |

Three things that catch people out:

**A project can have two of these and mean one.** A Tailwind config that only
re-exports CSS custom properties is not a second source — it is a view of the
first. Find which one a developer edits when a colour changes; that is the
source of truth, and the other is generated. Getting this backwards produces a
Figma file that is exact against a file nobody maintains.

**Tailwind's default palette is not the product's design system.** Extract what
the config *adds or overrides*, not the hundreds of stock colours inherited
from the framework.

**Semantic layers.** `--color-text-primary: var(--color-grey-900)` is an alias.
Figma variables model this natively — create the primitive, then a semantic
variable that references it. Resolve the chain before comparing values, or
every alias reads as a mismatch.

## Naming

Web naming is usually already kebab or dot-path, which maps to Figma's slash
groups more directly than camelCase does: `--color-text-primary` →
`color/text/primary`. Set the explicit map once for anything irregular and let
`token_diff.py` report the rest.

## Catalog

Storybook is the default and the reason this stack is cheap. Check for
`.storybook/main.*` and read its `framework` field.

Adding one: initialize with the framework's own generator, then apply the
contract in `storybook-generic.md` — required documentation fields on every
story (enforce it with a wrapper or a lint rule, since there is no compiler to
do it for you), a name-based two-way drift check, an exhaustive image export.

Alternatives that satisfy the same contract: Histoire (Vue), Ladle (React,
lighter).

## Images

`@storybook/test-runner` with Playwright is the standard path:

```bash
npx playwright install --with-deps chromium
npm run build-storybook
npx test-storybook --url http://127.0.0.1:6006 --maxWorkers=2
```

Capture per story with `page.screenshot`. Then, before trusting a single diff:

- **Freeze animation and transitions.** A CSS transition mid-flight makes the
  same story produce a different image every run and turns every comparison
  into noise. Inject a stylesheet that disables them globally at capture time.
- **Pin the fonts.** Wait for `document.fonts.ready`. A capture taken during a
  webfont swap is measuring the fallback face.
- **Pin the device pixel ratio** and record it as `referenceScale`. This is the
  ÷2 trap in its web form.
- **Guard against blank captures.** A story that threw during render still
  produces a valid PNG of nothing.
- Set a fixed viewport per story kind — a component grid and a full page want
  different surfaces.

## Flow tracing

| Router | Where the graph is |
|---|---|
| react-router | the route objects / `<Routes>` tree; then `navigate(` and `<Link to=` call sites |
| Next app router | the `app/` directory structure; then `router.push(` and `<Link href=` |
| Next pages router | `pages/`; same call sites |
| vue-router | the routes array; `router.push`, `<router-link>` |
| Angular | `RouterModule.forRoot` route config; `router.navigate` |

Guards map cleanly onto the `guard` edge kind: route loaders, middleware,
`beforeEnter` hooks, auth wrappers. Next middleware is a single file that
redirects for the whole app — model it as the guard node.

Every edge still needs `src` as `file:line`.

## Two web-specific realities

**Responsive.** The product has no single frame size. Pick the breakpoints you
will document, put them in the profile, and put the ones you are *not*
documenting in the scope not-doing list. Silently drawing only the mobile
width and calling the flow complete is the same defect as an unmeasured
number.

**Dark mode is usually real here**, unlike on many app codebases. If the tokens
have two modes, Figma variable modes map onto them one to one, and doing both
at token level costs almost nothing. Doing both at *screen* level doubles the
frame count — decide explicitly at intake.
