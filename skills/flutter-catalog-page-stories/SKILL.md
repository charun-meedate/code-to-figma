---
name: flutter-catalog-page-stories
description: Render full production Flutter screens inside a Widgetbook catalog without a backend — slim service-locator mocking, per-story dependency overrides, route-argument fixtures, and timer-safe headless tests. Use when a component catalog needs to grow from shared widgets to whole pages, or when screens resolve their dependencies from getIt/service locator inside build().
---

# Full-page stories on a service-locator app

Component stories take props; screens take nothing and *reach out* — `getIt<Repo>()`
inside `build()`, cubits created from the locator, arguments hard-cast from the
route. Rendering a page therefore means provisioning everything it reaches for.
This is the part of a catalog that looks like a day per screen and is actually
a day per *flow* once the pattern is set.

## Map the dependencies before writing anything

Per flow, grep every screen **and its cubit** for `getIt<`, `context.read<`,
`BlocSelector<` and write a matrix (screen × resolved-from-locator ×
read-from-context). Two traps that both bit in practice:

- **Indirect context reads.** A screen's file can say nothing while a child
  organism reads a cubit (terms links reading remote config three widgets
  down). Grep the screen's organisms too, or the matrix lies.
- **The "light" flow isn't.** An auth/splash flow looks trivial and pulls
  remote config, push services and chat session. Audit before estimating.

Keep the matrix as a README next to the flow's mock registrations — it is the
review artifact that justifies each stand-in.

## Stand-ins: three tiers, in order of preference

1. **`Fake` (mocktail) for what is never called.** Throws loudly on first use —
   which is a *feature*: that is how you discover a screen drives a path you
   didn't provision, instead of it silently no-opping.
2. **Real class + inert IO for what is driven.** Subclass the real cubit/use
   case and override only the methods that do IO, as state-only mutations. The
   catalog then behaves like the app (optimistic updates, status transitions)
   without a network.
3. **Genuine in-memory implementation where construction itself reads.** A
   cubit that reads storage *in its constructor* defeats both Fakes (throw) and
   overrides (too late) — give it a real in-memory storage.

Give every repository stand-in a `failing` flag (and finer flags where a flow
needs them — e.g. `failVerifyOnly` so the OTP *request* succeeds and only the
PIN check fails; otherwise the error state you wanted is unreachable because
the way there broke first).

## Per-story dependency overrides: locator scopes

Error states need a different repository for one story only. Widget-tree
injection can't reach dependencies resolved inside `build()` — but locator
scopes can (get_it's `pushNewScope`). A tiny StatefulWidget pushes a scope with
the override in `initState` and pops it in `dispose`; registrations shadow the
defaults only while that story is mounted:

```dart
LocatorScope(
  configure: (locator) => locator.registerLazySingleton<AuthRepo>(
    () => CatalogAuthRepo(failing: true)),
  child: const AuthScreen(),
)
```

## Frame the page

The workbench renders use cases under loose constraints; screens expect a
phone. Wrap each page story in a fixed-size frame (e.g. 390×844) that also
overrides `MediaQuery.size`, and clip. Scenario names, not state matrices:
a page's states are data-shaped ("Wrong PIN", "Maintenance mode"), and the
config-pinned states are often ones nobody can reach in the real app —
maintenance mode, forced update — which is half the value.

Route arguments (`state.extra as XxxArguments` casts) come from one fixtures
file, not invented per story, so screen and story agree on what "typical" is.

## Headless tests: the three failure modes

**1. Vacuous passes.** Opening a story via `initialRoute: '/?path=...'` fails
*silently* if the path doesn't parse — Widgetbook falls back to its welcome
page and your "renders X" test passes while rendering nothing. Two fixes, both
mandatory: `Uri.encodeQueryComponent` the path (a folder named "Auth &
Onboarding" puts a raw `&` in the query string), and assert the welcome page is
absent in every case. The day this guard landed it exposed that *all* page
stories had been passing without rendering.

**2. Real timers.** Screens arm timers at mount (an uncancelable
`Future.delayed` splash fallback; your own stand-in's response delay). Headless
tests fail on timers pending at teardown. Maintain a per-path settle map —
pump *past* the longest timer rather than excluding the story — and add one
short drain pump after any long pump: a long `pump(6s)` renders a single frame
at its end, and a completion listener firing on that frame can arm one more
short timer that would otherwise pend.

**3. Real production bugs.** Rendering real screens at real widths finds real
overflows — the first page flow here caught a Row overflowing 146px at a
standard phone width, in code that had shipped. Don't fix production from the
catalog branch and don't let the suite stay red: keep a
`knownProductionRenderIssues` map (path → one-line description + findings-doc
reference) and have the smoke test tolerate *exactly* that failure type for
those paths. Removing the entry re-arms the check when the fix lands. Record
the bug itself in a findings document that travels with the repo.

## Session/global cubits: overrides accumulate per flow

The app-wide seeded cubits (session, remote config…) start with no methods
overridden — every flow that drives a new method surfaces as a loud `Fake`
throw in the smoke test, and you add a state-only override for exactly that
method. This keeps the seeded cubits honest: they implement precisely what
some story exercises, nothing speculative.

## What the pilot flow teaches about estimates

The first flow costs ~2× any later flow: the reusable pieces (page frame,
locator scope, settle map, vacuous-pass guard, findings protocol) all get built
there. Estimate later flows by their matrix size, not by the pilot.
