# Web — React, Next, Vue, Svelte, Angular

One page, because Storybook covers all of them and the differences are in
where the tokens live, not in the method.

**Status: token extraction is field-proven; everything downstream is a
playbook.** The tokens tier has been run against four production codebases —
React Router 8 + Tailwind v4, Next 15 + Tailwind v3, and two Vite + TanStack
Router + Tailwind v4 apps — and the numbers quoted on this page are measured
from them. The catalog, capture and screen-comparison sections have not been
through a full programme here; where something is a recommendation rather than
a measured result, it says so.

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
| **Tailwind v4** | **`@theme` blocks in CSS** — there is no config file | `css-custom-property` |
| **Tailwind v3** | `tailwind.config.*` under `theme.extend` | see below — **not** a regex |
| **MUI / Chakra** | `createTheme(` / `extendTheme(` | see below — **not** a regex |
| **styled-components / Emotion** | a `theme.ts` object export | see below |
| **Panda, Stitches, vanilla-extract** | their config or `createTheme` call | see below |

**Nested theme objects cannot be regexed, and failing at it is silent.** The
`js-object-*` presets capture the leaf key only, so `brand.500` and
`accent.500` both extract as `500`, the second is dropped with a
"declared twice" warning that reads like harmless dedup, and the diff then
compares a partial set and calls it clean. Use them only for a genuinely flat
object.

For anything nested, dump the theme to JSON and use `format: "json-tree"`,
which joins the key path so `brand.500` and `accent.500` stay distinct:

```bash
node -e "const t=require('./tailwind.config.js');console.log(JSON.stringify((t.default||t).theme.extend))" > theme.json
```

```json
{ "color":      [{ "glob": "theme.json", "format": "json-tree", "rootKey": "colors" }],
  "typography": [{ "glob": "theme.json", "format": "json-tree", "rootKey": "fontSize" }] }
```

Verified on a 437-line production Tailwind v3 config: 41 colours, 150
typography entries and 10 shadows, with no collisions. A `fontSize` value is
an array — `['16px','26px']` — and both parts come out, the second as
`.../line-height`. If the config `require`s nothing, this runs without
`node_modules`.

**Tailwind v4 moved the theme into CSS.** Looking for `tailwind.config.js` on a
v4 project finds nothing and the obvious conclusion — "no Tailwind theme here"
— is wrong. Check the CSS for `@theme` and `@theme inline`. Measured on a real
shadcn + Tailwind v4 project: **531 custom properties across two files, of
which only 43% were directly usable values** — the rest were `var()` aliases
(260), `oklch()` (31) and `calc()` (6). With `--resolve-aliases` (which substitutes
references inside expressions too), `calc()` evaluation and oklch support, that
same project reads **100%**. Across three real web codebases the tier now
lands at 100% / 96% / 97% comparable; what is left over is font stacks and
animation shorthands, which are not scalars and are reported as such. Run the extraction both ways once:
the gap between the two numbers is the size of the semantic layer, which is
worth knowing before you model it in Figma.

`@theme inline` in particular is *always* an alias layer: `--color-primary:
var(--primary)`. The real values sit in a `:root` block, often in a different
file. Extract the `:root` layer for values, and model the `@theme` layer as
Figma variables that reference them.

**Do not point one family at both layers.** A config with a `:root` source and
a `@theme` source under the same family extracts every token twice — once as
`accent` and once as `color-accent` — and pushing that produces two Figma
variables per token, the second named `color/color/accent`. Caught on a real
push by reading the payload before writing it: 34 duplicates in 68 entries.
Extract the definitions; add the bridge as aliases afterwards, or leave it out
and say so.

Three more things that catch people out:

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
  produces a valid PNG of nothing. Asserting the file is over ~1KB catches it.
- Set a fixed viewport per story kind — a component grid and a full page want
  different surfaces.
- **Capture the viewport, not `fullPage`.** A full-page capture is as tall as
  its content, so its height moves with the data and it can never line up with
  a fixed Figma frame — the diff refuses it outright. `fullPage: true` is right
  for regression triage and wrong for design comparison. A field-tested project
  had exactly that: a well-built visual-smoke spec, unusable for frame
  comparison for that one reason.

Seen in the wild and worth copying: auth state and API stubs applied **per
route** before each capture, so every screenshot is a chosen state rather than
whatever the backend happened to return. That is the piece that makes web
capture competitive with a catalog.

## Flow tracing

| Router | Where the graph is |
|---|---|
| react-router v6 (library mode) | the route objects / `<Routes>` tree; then `navigate(` and `<Link to=` call sites |
| react-router v7+ (framework mode) | **`app/routes.ts`** — a real route manifest, plus file conventions under `app/routes/`. Presence of `react-router.config.ts` and `@react-router/dev` is the tell. This is the old Remix, renamed |
| Next app router | the `app/` directory structure; then `router.push(` and `<Link href=` |
| Next pages router | `pages/`; same call sites |
| vue-router | the routes array; `router.push`, `<router-link>` |
| Angular | `RouterModule.forRoot` route config; `router.navigate` |
| TanStack Router | **`routeTree.gen.ts`** — a generated, complete route tree, the easiest graph to trace of any router here. Read it rather than the `src/routes/` files; guards are `beforeLoad` on a route |

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
