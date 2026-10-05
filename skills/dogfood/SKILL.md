---
name: dogfood
description: "Exercise a real product journey as a user, collecting functional, UX, console/network, accessibility, and visual evidence that scripted happy-path tests can miss. Use before shipping meaningful UI/product flows or when the user asks for hands-on product evaluation."
argument-hint: "[journey/persona/scope] [--fix]"
disable-model-invocation: true
---

# Dogfood the product, not the test suite

Dogfooding asks whether a human can complete the intended job comfortably and coherently. It complements tests; it does not replace them.

Read `references/dogfood-protocol.md`, repository instructions, and the relevant spec/acceptance criteria. Reuse existing browser/E2E tooling when available instead of inventing a parallel harness.

## Run

Define the persona, starting state, intended job and success condition. Walk the journey from the user's entry point, including at least one relevant non-happy state when cheap: empty, loading, validation, permission, retry, cancellation or recovery.

Observe and capture only useful evidence:

- whether the job actually completes;
- confusing copy, navigation or interaction;
- console/runtime errors and failed or suspicious network requests;
- keyboard/focus/accessibility failures visible in the journey;
- visual overflow, layout breakage and bad responsive states;
- unnecessary friction or missing feedback.

Classify findings as `BLOCKER`, `FUNCTIONAL`, `UX`, or `POLISH`. Give each a reproduction path and evidence. Do not inflate subjective taste into a blocker.

## Fix mode

Without `--fix`, report findings only.

With `--fix`, fix only accepted, bounded findings. During an orchestrated Gearbox run, product changes remain worker-owned and must re-enter normal verification/review. Re-run only the affected journey after each repair; do not replay unrelated screens for reassurance.

Dogfood evidence may be referenced in the PR technical report, but screenshots alone never prove correctness.
