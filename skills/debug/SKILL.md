---
name: debug
description: "Diagnose and fix a bug from a tight red-capable feedback loop: reproduce, minimise, rank falsifiable hypotheses, instrument deliberately, fix the root cause, add regression protection, clean up, and capture reusable learning when warranted."
argument-hint: "[symptom, failing test, incident, or issue]"
disable-model-invocation: true
---

# Debug from a tight loop, not edit roulette

The goal is a root-cause fix with an evidence chain that can go **red** before the fix and **green** after it.

Read `references/secret-redaction.md` before handling logs, environment output, request traces or evidence.

## 1. Build the feedback loop first

Before forming a code-level theory, establish one command/harness that exercises the user's actual symptom.

Good loop shapes include:

- one focused test;
- a CLI/curl invocation with an assertion;
- a small replay of a captured request/event;
- a headless browser script;
- a throwaway harness around the real failing seam;
- a property/fuzz loop;
- a differential old-vs-new comparison;
- `git bisect run` when the regression window is known.

Tighten it until it is:

- **red-capable**: it can catch this exact bug, not merely “does not crash”;
- **deterministic enough**: flaky bugs have a raised/pinned reproduction rate;
- **fast**: seconds where reasonably possible;
- **agent-runnable**: no human click loop unless unavoidable.

Run the loop at least once before moving on and record only redacted output.

If you genuinely cannot build a red-capable loop, stop and state what is missing: environment access, a redacted trace/log/HAR, or permission for temporary instrumentation. Do not compensate with confident speculation.

## 2. Reproduce and minimise

Run the loop until the reported symptom is confirmed.

Then remove inputs, callers, config, state and steps one at a time. Re-run after each cut.

Stop minimising when every remaining element is load-bearing for the failure. The minimal repro narrows the hypothesis space and is the preferred seed for the regression test.

## 3. Compete hypotheses

Create 3-5 ranked **falsifiable** hypotheses before testing the first plausible idea.

For each:

```text
If <cause> is true, then <specific probe/change> should produce <observable result>.
```

Discard “vibes” that do not predict an observation.

Show the compact ranked list to the user when their domain knowledge could cheaply re-rank it. Do not block an AFK run waiting for acknowledgement.

## 4. Instrument one prediction at a time

Prefer, in order:

1. debugger/REPL inspection;
2. narrow targeted instrumentation at a discriminating boundary;
3. focused traces/queries/metrics.

Do not “log everything and grep”.

Tag temporary debug output with a unique prefix such as `[DEBUG-a4f2]` so cleanup is mechanical.

For performance regressions, establish a measured baseline/profiler/query plan before changing code.

Every captured command/output stored in Gearbox artifacts must be redacted. Never echo a credential-bearing environment variable just to inspect it.

## 5. Fix the root cause and lock it down

Once evidence selects a cause:

1. turn the minimised repro into a regression test **before** the fix when a correct stable seam exists;
2. watch it fail;
3. apply the smallest fix restoring the violated invariant;
4. watch the regression test pass;
5. rerun the original un-minimised Phase 1 loop.

If no correct test seam exists, say so explicitly. A too-shallow fake regression test is worse than documenting that the architecture lacks a stable seam. Consider this a codebase-design/retro candidate.

Check sibling paths only when evidence shows they share the root cause.

## 6. Cleanup and completion

Before declaring success:

- original feedback loop is green;
- regression test is green, or the missing seam is documented;
- neighboring configured checks are green enough for the risk;
- every temporary `[DEBUG-...]` probe is removed;
- throwaway harnesses are removed or intentionally kept in a clearly named debug/test location;
- stored evidence/log summaries contain no raw sensitive values.

Finish with:

```text
symptom → red loop → minimal repro → decisive evidence → root cause → fix → regression protection → remaining uncertainty
```

## Compound or retro?

Recommend `/gearbox:learn` when the debugging session revealed a reusable truth about the system: hidden invariant, misleading architecture, recurring operational trap, or non-obvious failed approach.

Recommend `/gearbox:retro` when the pain came from the **agent environment**: missing fast repro tooling, poor observability, repeated navigation, unavailable fixtures, or a deterministic check that should exist.

A normal bug fix needs neither.
