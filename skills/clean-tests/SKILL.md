---
name: clean-tests
description: "Audit and safely reduce a test suite by finding redundant, obsolete, superseded, implementation-coupled, or low-value tests without weakening meaningful behavioral coverage. Default is report-only; use --apply to merge/delete/rewrite proven cleanup candidates."
argument-hint: "[scope/path/domain] [--apply]"
disable-model-invocation: true
---

# Remove test-suite noise without removing confidence

Read `references/test-suite-cleanup.md` and `references/test-credibility.md`.

The goal is not fewer tests. The goal is less maintenance/runtime noise for the same or stronger ability to detect meaningful faults.

Default behavior is **report-only**. Classify candidates as `KEEP`, `MERGE`, `DELETE`, `REWRITE`, or `BLOCKED`. Only `--apply` authorizes mutation.

Always delegate the audit to the fresh `test-curator` agent. Give it the requested scope, repository test conventions, relevant current specs/contracts, test commands, and permission state. Do not ask an implementation agent to grade tests it just wrote.

Before proposing deletion or merge:

1. establish a green targeted baseline;
2. name the behavior/invariant each candidate protects;
3. identify the surviving test(s) that protect the same failure mode, or prove the behavior is no longer required;
4. apply the credibility gate to both candidate and survivor;
5. for important invariants, use a targeted mutation/fault story and run mutation tooling when available;
6. reject cleanup when coverage equivalence is ambiguous.

Age, slowness, flakiness, low coverage, or the existence of an E2E test are not sufficient deletion evidence by themselves.

With `--apply`, mutate only tests, test fixtures and test-only helpers within scope. Do not modify production code to make cleanup convenient. Apply small batches, rerun focused tests after each batch, then run the affected repository-native suite/checks.

Report before/after test count and runtime when cheaply measurable, but never optimize those numbers at the cost of fault detection.

After meaningful cleanup of a high-value invariant, use `references/test-hardening.md` when targeted mutation/property checks would materially increase confidence in the surviving suite.
