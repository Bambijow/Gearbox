---
name: debug
description: "Diagnose and fix a bug from evidence: reproduce, narrow, form falsifiable hypotheses, fix the root cause, add regression protection, and capture reusable learning when warranted."
argument-hint: "[symptom, failing test, incident, or issue]"
disable-model-invocation: true
---

# Debug from evidence, not edit roulette

The goal is a root-cause fix with a clear evidence chain.

## 1. Establish the symptom

Read repository instructions and `.gearbox/config.md` if present. Inspect the relevant code, logs, tests, and recent changes. Redact secrets before repeating any logs or environment values.

Reproduce the failure when practical. If direct reproduction is impossible, construct the closest deterministic evidence: a failing test, minimal input, trace, query, or state snapshot.

Write down the difference between **expected**, **observed**, and **unknown**.

## 2. Narrow the fault domain

Trace the failing path from boundary to invariant. Check assumptions at seams: inputs, serialization, state transitions, retries, caches, clocks, concurrency, permissions, network boundaries, migrations, feature flags, and environment differences.

Use binary narrowing where possible. Instrument temporarily when observation is cheaper than speculation. Remove temporary instrumentation before finishing unless it has lasting operational value.

## 3. Compete hypotheses

Maintain a small ranked set of falsifiable hypotheses. For each, state what evidence would support or reject it. Run the cheapest discriminating check first.

Do not patch the first suspicious line merely because it is nearby.

## 4. Fix the root cause

Once evidence identifies the cause, make the smallest fix that restores the violated invariant. Add a regression test at the narrowest stable seam that would have caught the bug without hardcoding internals.

Check for sibling paths that share the same root cause. Fix them only when the evidence shows they are genuinely affected.

## 5. Verify broadly enough

Run the regression test, relevant neighboring tests, and configured checks appropriate to the changed area. Reproduce the original scenario again if possible.

## 6. Decide whether this should compound

Invoke or recommend `/learn` only when the investigation uncovered a non-obvious reusable lesson: a hidden invariant, misleading architecture, recurring failure mode, operational trap, or prevention rule. Do not create a learning note for ordinary typo-level bugs.

Finish with a concise evidence chain: symptom → decisive evidence → root cause → fix → regression protection → remaining uncertainty.
