---
name: test-harden
description: "Stress important tests with targeted mutation, property/invariant checks, and bounded fuzzing to find false confidence after ordinary tests are green. Use for high-cost invariants, parsers, state machines, auth/money/data-integrity logic, or when test credibility is uncertain."
argument-hint: "[scope/test/invariant] [--apply]"
disable-model-invocation: true
---

# Harden tests against plausible faults

Start from green tests and a named invariant. This skill asks a harder question: would the tests detect a realistic wrong implementation?

Read `references/test-hardening.md` and `references/test-credibility.md`. Detect repository-native mutation/property/fuzz tools before adding dependencies.

## Sequence

1. Name the invariant and the tests that claim to protect it.
2. Pick a small set of plausible mutations from the actual implementation seam.
3. Run mutations only against the bounded target when tooling permits.
4. Treat surviving meaningful mutants as evidence of a test gap, not automatically a product bug.
5. Add property/invariant tests when examples under-specify a rule.
6. Use fuzzing only where generated inputs exercise a meaningful parser/state/input space and a bounded oracle exists.
7. Re-run the ordinary targeted suite after hardening.

Prefer three discriminating mutants over thousands of mechanical ones. Ignore equivalent/trivial mutants explicitly rather than gaming a score.

Without `--apply`, return the hardening design and gaps. With `--apply`, add or strengthen tests through the normal Gearbox mutation boundary when an orchestrated run is active.

Do not chase 100% mutation score, coverage, or random-input volume. Stop when important plausible faults are killed, the invariant is credibly protected, or the remaining gap requires architecture rather than more tests.
