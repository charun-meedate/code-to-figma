# Discovery — what to find out before you ask anything

Run this before the intake. Every question you can answer from the repository
is a question the human should not have to answer, and every question you
*cannot* answer from the repository is one you must not guess at.

Each step writes into `project-profile.json` with a confidence:

- **detected** — a file says so. Render it in the intake as "I found X — confirm?"
- **inferred** — you concluded it from indirect evidence. Render it as "I believe
  X because Y — correct?"
- **unknown** — ask openly.

Three answers are confirmed with the human **even when detected**, because
each one was a human decision on the proven run and getting it wrong is
expensive: the build flavour/variant, the target Figma file, and whether the
organisation's existing design-system library may be used.

Write a citation into `evidence` for every detected field. A field with no
citation and no human answer must stay `null`.

## Contents

- D1 · Framework
- D2 · Runner, variants, environment
- D3 · Token sources, per family
- D4 · Catalog
- D5 · What a harness would have to stand in for
- D6 · How images will be produced
- D7 · Design side
- D8 · Text script
- Reporting back

---

## D1 · Framework

**Test in this order and stop at the first match.** The order is the whole
point: nearly every specific framework also declares its base framework, so an
unordered check routes React Native to the web playbook, where not one
instruction applies.

| # | Signal | Verdict |
|---|---|---|
| 1 | `pubspec.yaml` containing a `flutter:` key | Flutter |
| 2 | `package.json` with `react-native` or `expo` | **React Native** → `stacks/native-mobile.md`, not web |
| 3 | `package.json` with `next` / `nuxt` / `@remix-run/*` / `astro` | Next / Nuxt / Remix / Astro → `stacks/web.md` |
| 4 | `package.json` with `react`/`react-dom` / `vue` / `svelte` / `@angular/core` / `solid-js` | React / Vue / Svelte / Angular / Solid → `stacks/web.md` |
| 5 | `*.xcodeproj`/`Package.swift` plus `import SwiftUI` | SwiftUI |
| 6 | `build.gradle(.kts)` with `androidx.compose` **or** a `libs.versions.toml` declaring a compose coordinate | Compose |
| 7 | none of these | the unknown-stack path — `stacks/unknown.md` |

Row 6 needs the version-catalog check because a Gradle build using one reads
`implementation(libs.compose.ui)`, and the `androidx.compose` string never
appears in the build file at all.

A framework not in the table is not a failure — take the unknown-stack path,
which ends by writing a playbook for it.

Several hits in different directories means a monorepo: ask which package is
in scope before anything else, and record it as `stack.monorepoPackage`.

## D2 · Runner, variants, environment

- Flutter: `.fvmrc` present → the prefix is `fvm flutter`, otherwise `flutter`.
  Flavours appear in `android/app/build.gradle` (`productFlavors`), in iOS
  schemes, and as `main_*.dart` entry points. Grep `.vscode/launch.json`,
  `Makefile`, CI config and `scripts/` for `--dart-define`.
- JS: the `packageManager` field wins; otherwise the lockfile
  (`pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `bun.lockb` → bun, else npm).
  Record `scripts.dev`, `scripts.build`, `scripts.storybook`, `scripts.test`.
- Note which environment variables the app refuses to start without, and what
  a safe placeholder is. A catalog build that cannot boot is not a catalog.

## D3 · Token sources, per family

Do this per family — `color`, `spacing`, `radius`, `typography`, `shadow`,
`opacity` — and record `present`, `partial` or `absent` **with evidence either
way**.

| Stack | Where to look, in order |
|---|---|
| Flutter | `ThemeExtension<…>` subclasses; `final Color …;` / `final TextStyle …;` / `final double …;` under `lib/**/{styles,theme,tokens}/`; `ColorScheme(`; `TextTheme(` |
| React / web | `tokens.json` or `*.tokens.json` with `$value` (W3C DTCG); `--custom-property:` inside `:root {` in CSS/SCSS; `tailwind.config.*` under `theme.extend`; `createTheme(`/`extendTheme(` for MUI or Chakra; a `theme.ts` exporting an object of literals; `panda.config`, `stitches.config`, vanilla-extract `createTheme` |
| SwiftUI | `*.xcassets/**/Contents.json` colour sets; `extension Color`; `Font.custom(` |
| Compose | `val X = Color(0xFF…)`; `Typography(`; `lightColorScheme(`/`darkColorScheme(` |

Then two things that are as important as what you found:

**The absence probe.** A family with no central definition is not a family you
should invent. Count the scattered literals — e.g. `grep -rc "BoxShadow(" lib/`
across many files with no token class — and record `status: absent` plus
`absenceEvidence`. On the proven run the product had **no shadow token layer
at all** while shadows appeared inline in twenty files; the four shadow styles
that ended up in Figma were a consolidation of scattered values, and saying so
was part of the deliverable.

**The hardcoded-value scan.** Count colour literals living outside the token
files. That number is the honest prior for how much of the product actually
uses its own design system, and it belongs in the findings.

**Fallback when nothing matches.** Ask for one to three token files. Read them,
derive a regex, run `extract_tokens.py`, and **echo the count plus five samples
back for confirmation before using it.** Write the confirmed regex into the
profile. A regex per family is the portable primitive here — it is how the
same check worked on the proven run, and it is why an unfamiliar stack costs a
conversation rather than a rewrite.

## D4 · Catalog

| Signal | Tool |
|---|---|
| `widgetbook` in dev dependencies + a `widgetbook/` directory | Widgetbook |
| `.storybook/main.*` (read its `framework` field) | Storybook |
| `histoire.config.*` / ladle config | Histoire / Ladle |
| SwiftUI `#Preview` / `PreviewProvider` only | **none** — previews cannot be exported in bulk |

Also record whether it can produce images today: `@storybook/test-runner` or
`playwright` in dependencies, a `test-storybook` script, or an existing
screenshot/golden test on the Flutter side. A catalog with no export is half
the instrument.

## D5 · What a harness would have to stand in for

- **Dependency injection** — `get_it`/`injectable`, Riverpod, Provider, a React
  context. The decisive probe is whether components resolve dependencies
  *inside* `build`/render rather than receiving them: grep for the locator call
  inside view files. If they do, per-story scope overrides are mandatory, not
  optional.
- **Router** — `go_router`, `auto_route`, `react-router`, the Next `app/`
  directory, `vue-router`. Record the route-table files: they are the source
  for `flow-edges.json` later.
- **i18n** — `slang.yaml`, `l10n.yaml` + ARB, `i18next`, `next-intl`. Record the
  locale list and which one the product ships as primary; that decides D8.
- **Global state** every screen assumes exists (a session, a feature-flag
  store, a connectivity watcher).

## D6 · How images will be produced

Derive it, do not ask it first:

| Situation | Mechanism |
|---|---|
| Flutter + catalog | render every story to PNG in a test — the proven path |
| Web + Storybook | `@storybook/test-runner` with Playwright |
| Web, no Storybook | Playwright against the dev server |
| Native, no catalog | simulator/emulator capture, driven — see `evidence-without-storybook.md` |
| Nothing available | code-only; say so in the acceptance criteria |

Record the expected `referenceScale`. Then **calibrate before measuring
anything**: take one element of known size in a real reference image and
confirm the ratio. Set `scaleCalibrated: true` only after that. A forgotten
÷2 produces a component at exactly double size — smooth, plausible, and
review-proof.

## D7 · Design side

- An existing `tokens.config.json` means the reverse pipeline
  (`figma-token-export`) is already in use here. Do not fight it: that tool
  owns Figma→code; this one owns code→Figma. Say which direction is
  authoritative before either runs.
- Code Connect configuration, if any.
- Fonts: `fontFamily:`, `GoogleFonts.`, `@font-face`, font assets in the
  manifest → the exact families **and weights** the code uses. This is the P0
  gate: the font must exist in Figma at those weights before a single frame is
  drawn.

## D8 · Text script

Scan the primary locale's strings for Thai (U+0E00–0E7F), Lao, Khmer or
Burmese. Any hit sets `text.segmentationRequired` — Figma has no line-break
dictionary for these and raw text breaks mid-word. CJK does not need this.

## Reporting back

Before the intake, tell the human in a few lines: the stack, the token
families found and any found *absent*, whether a catalog exists, and what will
produce the images. Then ask the two intake questions with those findings
pre-filled. Do not present a discovery as a decision — the human still gets to
say no.
