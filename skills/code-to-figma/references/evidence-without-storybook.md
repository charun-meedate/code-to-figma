# When there is no catalog

Read this on the no-catalog branch at screens scope. Two options, both weaker
than a catalog, both usable if you say plainly which one you took.

Tokens and flows do not need this page at all. Token values come from source
files; flow edges come from router files. Neither ever needed a rendered
image, and skipping the catalog costs them nothing.

What it costs is **screens**. A catalog is the only thing that renders a
component in a state the product cannot easily be pushed into — a failed
request, an empty list, a name too long for its container, a permission
denied. On the proven run those states were the majority of the work: 16
screens produced 59 frames. Without a catalog most of that is out of reach.

## Option 1 · Drive the real app and capture

The stronger of the two. Launch the app, navigate to each screen, screenshot.

**Do not drive it with deep links from outside the app.** Mobile platforms put
a confirmation dialog in front of an externally-opened custom-scheme URL. That
dialog lands in the screenshot, survives an app restart because the system
owns it, and on the proven run the only way out was rebooting the simulator.
The working approach was to drive the app **from inside itself** — evaluate
navigation calls in the running process, through whatever debug or automation
channel the platform offers — which also lets you set the session state that
a redirect guard is checking, instead of fighting it.

Whatever the channel, always **read back where the app actually landed.** A
router guard may have sent it somewhere else, and a screenshot of the wrong
screen is worse than no screenshot.

Limits, and they are not small — **on native.** Read the web note below before
applying them there.

- **Error, empty and loading states are mostly unreachable.** You cannot ask a
  live backend to fail on demand.
- **Data varies between captures**, so a strict image comparison produces noise.
  Compare structure — order, spacing rhythm, colour, type, presence and
  absence of elements — not pixels.

### On the web, those two limits mostly do not apply

This page originally stated them as universal. That was wrong, and a real
codebase corrected it: a browser lets you intercept every request, so a
Playwright run can return a 404, an empty list or a slow response on demand,
and can set auth state per route. The field-tested project did exactly that —
six routes at two viewports, each with its own auth state and API stubs, plus
an empty-state spec alongside.

So on the web the no-catalog path is **much closer to a catalog than the rest
of this page implies**: you get forced states and deterministic data. What you
still do not get is a component in isolation, or the exhaustive enumeration a
drift check gives you. Say that, rather than the two limits above.

If you find a project already screenshotting its routes in an e2e suite, that
is your evidence base — do not propose building a catalog before looking.
- **You need a reachable environment and a test account.** On the proven run
  the development environment pointed at a host that did not resolve, which
  was enough for the pre-login screens and stopped everything after them.
  That limitation was recorded per screen as deferred, never quietly skipped.

## Option 2 · Read the code

The weakest path, and legitimate if declared. Build the frame from the
component source: structure from the tree, values from the tokens, copy from
the string files.

Everything in §A of the acceptance criteria still holds — those are all
measured from code anyway. What you lose is the check that the code's
intentions survive contact with a layout engine. On the proven run a pin box
declared a width of 56 and rendered at 48, because six of them did not fit;
the declared number had never once taken effect. Nothing in the source says
so. Only a render does.

So on this path, add to the criteria: *"Screen structure is verified against
code reading only. No rendered reference exists. Render-time divergences — a
declared value the layout cannot honour — cannot be detected."* Then log any
you happen to find as unverifiable rather than confirmed.

## Say which one, in writing

The evidence statement at the bottom of `acceptance-criteria.md` is not
optional and is not boilerplate. Someone reading the signed document later has
to be able to tell how much verification stands behind it. All three levels
are legitimate claims. They are not the same claim, and the difference is
invisible in the Figma file itself.

## The cheap middle path

Before settling for code-only, check whether the stack can rasterize **one
component** without a full catalog — a widget test that renders to an image, a
component test with a screenshot, a single-story page. Most can. That gets you
a real render for the components that matter most, at a fraction of a
catalog's cost, and it is often enough to validate the pilot.

If you find yourself building enough of that to cover a flow, you are building
a catalog. At that point build it properly and read `storybook-generic.md`.
