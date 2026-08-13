# Web — React, Next, Vue, Svelte, Angular

One page, because Storybook covers all of them and the differences are in
where the tokens live, not in the method.

**Status: playbook, not proven.** The method transferred from a run on another
stack; the mechanics below are the standard tooling for these frameworks and
have not been through a full programme here. Where something is a
recommendation rather than a measured result, it says so.

## Contents

- Token sources, most to least authoritative
- Naming
- Catalog
- Images
- Flow tracing
- Two web-specific realities

---

## Token sources, most to least authoritative

| Shape | Where | Preset |
|---|---|---|
| **W3C DTCG** `tokens.json` with `$value` | anywhere; often `tokens/` | `dtcg-json` |
| **CSS custom properties** | `:root {}` in a global stylesheet | `css-custom-property` |
| **Tailwind** | `tailwind.config.*` under `theme.extend` | see below — **not** a regex |
| **MUI / Chakra** | `createTheme(` / `extendTheme(` | see below — **not** a regex |
| **styled-components / Emotion** | a `theme.ts` object export | see below |
| **Panda, Stitches, vanilla-extract** | their config or `createTheme` call | see below |

**Nested theme objects cannot be regexed, and failing at it is silent.** The
`js-object-*` presets capture the leaf key only, so `brand.500` and
`accent.500` both extract as `500`, the second is dropped with a
"declared twice" warning that reads like harmless dedup, and the diff then
compares a partial set and calls it clean. Use them only for a genuinely flat
object.

For anything nested, have the project print its resolved theme as JSON and
walk that instead — the values are already resolved, which also solves the
alias problem below:

```bash
node -e "const t=require('./tailwind.config.js');console.log(JSON.stringify((t.default||t).theme.extend))" > /tmp/theme.json
```

Then extract with a small walk that joins the key path with `/`, the way the
`dtcg-json` handler already does.

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

`@storybook/test-runner` with Playwright is the standard path. **A static build
does not serve itself** — the runner needs something listening on the URL you
give it:

```bash
npx playwright install --with-deps chromium
npm run build-storybook
npx concurrently -k -s first \
  "npx http-server storybook-static --port 6006 --silent" \
  "npx wait-on tcp:6006 && npx test-storybook --url http://127.0.0.1:6006 --maxWorkers=2"
```

**The runner takes no screenshots by default and hands you no `page`.** All of
it — the capture, and all four guards below — goes in a `postVisit` hook in
`.storybook/test-runner.ts`:

```ts
import type { TestRunnerConfig } from "@storybook/test-runner";
const config: TestRunnerConfig = {
  async postVisit(page, context) {
    await page.addStyleTag({ content: `*,*::before,*::after{
      animation:none!important;transition:none!important;caret-color:transparent!important}` });
    await page.evaluate(() => document.fonts.ready);
    const buf = await page.screenshot({ path: `gallery/${context.id}.png` });
    if (buf.length < 1000) throw new Error(`blank capture: ${context.id}`);
  },
};
export default config;
```

Check the Storybook major first: on 9, `@storybook/test-runner` is the legacy
path and a freshly initialized project gets the Vitest addon instead. Then,
before trusting a single diff:

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
