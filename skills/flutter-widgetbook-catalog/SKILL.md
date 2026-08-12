---
name: flutter-widgetbook-catalog
description: Build a Widgetbook component catalog ("Storybook") on an existing production Flutter app, so design and development share one reference rendered from real code. Use when asked for a component catalog, storybook, design-system reference, or living style guide for a Flutter codebase — especially when the app has custom ThemeExtensions, i18n, GoRouter, or flavors.
---

# Widgetbook catalog on a production Flutter app

Building a catalog for an app that already exists is mostly *harness* work, not
story work. Stories are easy; what breaks is the ambient scaffolding a real
widget expects — the theme, translations, a router, a Navigator. Get the
harness right first and the rest is mechanical.

Everything below was verified against widgetbook 3.25 / Flutter 3.44.

## Non-negotiable first step: prove the harness before writing stories

Write the harness plus **one self-test story**, run it on a device, and confirm
each ambient dependency resolves. Writing 40 stories against an unproven
harness means fixing 40 stories.

A self-test story is worth keeping permanently — it names which piece broke
instead of surfacing as a confusing crash inside an unrelated story. Give it a
row per dependency: theme tokens, typography/custom font, icon/SVG assets,
translations, locale-dependent date formatting, navigation intercept, and
dialog + bottom sheet.

## Wrapping order — the thing that surprises everyone

Widgetbook builds `appBuilder(context, <addons wrapping the use case>)`.
**The addons are INSIDE what your appBuilder returns.**

Consequences:

- A `MaterialApp` in your appBuilder does **not** shadow `MaterialThemeAddon` —
  the addon's `Theme` is deeper, so it wins. Putting a MaterialApp there is
  safe and gives you Navigator, Overlay, Directionality and MediaQuery.
- Do **not** set `theme:` in that MaterialApp. Let the addon own it, or the
  Light/Dark switch stops working.

Verify this in the installed package rather than trusting docs
(`workbench.dart` in the widgetbook source) — it is the load-bearing
assumption of the whole harness.

## The appBuilder stack

Outermost → innermost:

1. Translation/localization provider (so global i18n getters resolve)
2. `MaterialApp` — `navigatorKey`, `scaffoldMessengerKey`, locale, and the
   localization delegates copied from the app's real root
3. Router scope (below)
4. `Scaffold(backgroundColor: Colors.transparent, body: child)` — required so
   SnackBars can register; it also supplies the `Material` ancestor `InkWell`
   needs

**Localization delegates are not optional.** Any story formatting a date in a
non-default locale throws `LocaleDataException` without them. Loading the
delegates installs all locales' date symbols.

Also mirror the app's pre-`runApp` setup in the catalog entrypoint (plural
resolvers, `Intl.defaultLocale`, locale pinning). Prefer the *synchronous*
variants — the catalog's first frame should already be correct.

## Router stub

Production widgets call `context.push/go/pop/canPop` everywhere; without a
router in the tree they throw. Install a stub via the router package's
inherited widget.

- Override **every** entry point, not just `go`/`push`/`pop`: also `goNamed`,
  `pushNamed`, `pushReplacement`, `pushReplacementNamed`, `replace`,
  `replaceNamed`, `canPop`, `namedLocation`. Real widgets use the long tail.
- Report intents as a SnackBar — this doubles as live documentation of where a
  control leads.
- **`pop` is the exception**: if the shell's navigator can pop (a dialog or
  sheet is open), pop for real, so close buttons work.
- **`canPop` should return `true`.** Widgets that hide a back button when it is
  false would misrepresent themselves in the catalog.
- Check the constructor: in go_router the unnamed `GoRouter()` is a *factory*,
  so `extends GoRouter` must chain to a generative one
  (`super.routingConfig(...)`), and the route list must be non-empty.

## Story conventions

Two use cases per component:

- **Overview** — a static matrix of every variant and state that genuinely
  exists in the widget's code, each row labelled. Deterministic, so it also
  works as a screenshot/reference frame.
- **Playground** — the props on knobs, for edge inputs (long strings in the
  product's real language, extreme text scale).

Organisms and pages get named **scenario** use cases instead ("Text post",
"Sold out") — their state space is data-shaped, not enum-shaped.

Force documentation through the type system with a factory whose docs are
required parameters:

```dart
WidgetbookComponent documentedComponent({
  required String name,
  required String whenToUse,     // required → no story ships undocumented
  required List<String> props,
  required WidgetBuilder overview,
  WidgetBuilder? playground,
})
```

Render `whenToUse`/`props` in a **collapsible** header above the Overview, so
the matrix underneath stays a clean frame.

## Addon gotchas

- `DeviceFrameAddon` is deprecated → `ViewportAddon`. It has **no automatic
  "none" option** and its initial value is hard-coded to `viewports.first`, so
  put the none-viewport first or every story opens inside a device frame.
- `ViewportAddon` adds no inner Navigator (the old device frame did) — your
  MaterialApp must provide it.
- `context.knobs.list` / `listOrNull` are deprecated → `object.dropdown`,
  `object.segmented`, `objectOrNull.*`. `double.slider` / `int.slider` are
  fine. Knobs take a `description:` — use it for per-prop docs.
- Addons nest in list order: first = outermost. Put the theme first.

## Location and conventions

A root-level `widgetbook/` directory sharing the app's pubspec is simplest: the
asset manifest and fonts come along automatically, and there is no second
dependency graph to keep in sync. Check the analyzer config actually covers it
(you want it linted), and note that lints like `always_use_package_imports`
typically only apply inside `lib/`, so files there use relative imports between
themselves and `package:` imports for app code.

Decide explicitly which project rules apply inside the catalog and **write it
where reviewers will read it** (the contributing/agent guide, not just the PR
description). Design-token, i18n and lint rules should apply — stories are
copy-paste references. Test-id and state-management rules generally should not:
the harness is not a shipped feature.

Sample content (usernames, captions, image URLs) is **data**, not product copy.
Keep it in a fixtures file inside the catalog; never add catalog-only strings
to the app's translation files.

## Tests — two guards worth having from day one

**Smoke test.** Pumping the Widgetbook root proves nothing: with no story
selected it renders only the welcome page, skipping your appBuilder and addons
entirely. Instead enumerate the use cases and open each through Widgetbook's
own routing:

```dart
final useCases = WidgetbookRoot(children: buildCatalogDirectories())
    .leaves.whereType<WidgetbookUseCase>();

for (final useCase in useCases) {
  testWidgets('renders ${useCase.path}', (tester) async {
    await tester.pumpWidget(Widgetbook.material(
      appBuilder: catalogAppBuilder,
      directories: buildCatalogDirectories(),
      addons: buildCatalogAddons(),
      initialRoute: '/?path=${useCase.path}',
    ));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    expect(tester.takeException(), isNull);
  });
}
```

Use **bounded pumps, never `pumpAndSettle`** — shimmer and countdown widgets
animate forever and would hang the suite. Export `directories`, `addons` and
the appBuilder as top-level declarations so the app and the test share them.

A use-case path is the lowercased, dash-joined sidebar trail.

**Drift tests.** A hand-maintained catalog claiming to be the source of truth
needs enforcement, or it silently rots:

- *Registry drift*: file names in the shared-widget folder vs `*_stories.dart`
  files in the story folder, compared as sets, both directions.
- *Token drift*: token names parsed from the theme source vs the names
  documented in the Foundation pages.

**Prove the guard fails.** Delete a story, run the test, confirm it goes red
and names the gap, then restore. A drift test that cannot fail is decoration.

## Running it

If the app is flavored, `flutter run -t widgetbook/main.dart` alone fails —
mirror the flavor and dart-defines from the project's launch config. A
`--dart-define` for the initial story path is a cheap quality-of-life win:

```sh
flutter run --flavor dev --dart-define-from-file .env.dev \
  --dart-define=CATALOG_STORY=components/atoms/appcard/overview \
  -t widgetbook/main.dart
```

Set a sensible default initial route so the catalog opens on your own content
rather than Widgetbook's generic welcome page.

## Widgets that read state instead of taking it

In a mature app a minority of shared widgets pull state from the widget tree or
a service locator rather than accepting props. They are the ones that block a
catalog, and they are worth doing properly rather than skipping.

**Subclass the real cubit; don't mock it.** Override only the methods that
perform IO and keep the rest, so the component behaves as it does in the app —
a like button that doesn't fill when tapped documents the component wrongly.
Optimistic-update code is usually exactly what you want to keep; the request,
its debounce and its rollback are what you drop.

For the constructor dependencies you're not exercising, `Fake`-style stand-ins
(mocktail's `Fake`, or your own `noSuchMethod` stubs) are fine and *better* than
no-op implementations: if a future story does call one, it throws loudly rather
than quietly doing the wrong thing.

Two mistakes that cost real time:

- **Register under the base type.** Provider lookups match on the exact generic
  argument, so providing `SeededSessionCubit` leaves every
  `context.read<SessionCubit>()` failing.
- **Providers alone are not enough.** Some widgets bypass the provider and ask
  the service locator directly (`getIt<SessionCubit>()` mid-`build`). Register
  in both, and hand the provider the *same instance* the locator holds — one
  shared instance also means a follow tapped in one story updates every other
  story showing that person, which is the honest behaviour.

Stories needing a state other than the shared default should provide their own
cubit locally rather than mutating the shared one.

Dev-only dependencies (mocktail and friends) are importable from a root-level
catalog directory, the same as from `test/`.

## Access for people without a Flutter toolchain

The catalog is for designers too, and "run it on a simulator" excludes them.

**Check whether the app can build for web before promising a hosted URL.** On a
mature app it usually cannot: any `dart:io` in the reachable graph is fatal, and
atoms are often coupled upward (to routing, to organisms, to platform packages)
in ways that drag the entire app in. Probe it cheaply — build a trivial
entrypoint importing only the theme, confirm that works, then build the catalog
and read which files fail. Trace the import chain before concluding anything;
the culprit is rarely where the error points.

If web is out, **render the stories to images and publish those**. It runs on
the same engine the app ships on, so it survives whatever plugins later stories
pull in — which matters, because a catalog that grows to cover real screens will
only get less web-compatible.

Recipe that works:

- Run it under `flutter test` (that is what supplies an engine), in a file
  *without* the `_test.dart` suffix so it stays out of the normal suite.
- Render through the catalog's **preview route** (`?path=…&preview=true` in
  widgetbook) — you get the harness, addons and knobs, without the chrome.
- Pass a **single theme** in the addon list per pass instead of encoding addon
  settings into the query string; run once per theme.
- **Load fonts explicitly** with `FontLoader` — the app's font *and* the icon
  font — or you capture placeholder boxes.
- Capture a `RepaintBoundary` via `toImage`, inside `tester.runAsync`.
- Render on a surface taller than the longest story, then **crop the uniform
  run at the bottom** by scanning rows against the background pixel. Otherwise
  short stories trail a screenful of empty space.
- Emit an `index.html` grouped by the sidebar tree, and publish it from CI on
  the default branch.

## Practical warnings

- **Never edit source while a build is running.** The compiler reads files
  mid-flight and fails on a half-applied rename. Writing *new, not-yet-imported*
  files is safe; editing imported ones is not.
- Sequence the work: harness → foundation tokens → themed framework widgets →
  atoms → composites → pages. Each tier is a reviewable increment.
- Rendering full **screens** is a different problem: screens typically resolve
  dependencies from a service locator inside `build()`, so you need a slim
  bootstrap registering fakes in the same slots — not just a seeded session.
  Budget for it separately and audit one screen's real dependency list before
  estimating a whole flow.
